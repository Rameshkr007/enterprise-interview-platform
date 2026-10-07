from __future__ import annotations

from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    FileTooLargeException,
    NotFoundException,
    UnsupportedFileTypeException,
)
from app.models.resume import CandidateSkill, Resume, ResumeChunk, ResumeSection
from app.services.audit_service import record_audit_event
from app.services.embedding_service import EmbeddingService
from app.services.resume_parser_service import ResumeParserService
from app.services.semantic_chunker import SemanticChunker
from app.services.skill_extractor import SkillExtractor
from app.services.storage_service import StorageService
from app.utils.pdf_parser import PdfParser

log = structlog.get_logger(__name__)

MAX_RESUME_SIZE = 15 * 1024 * 1024  # 15 MB
ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}


class ResumeIntelligenceService:
    """Orchestrator for text extraction, layout sectioning, semantic chunking, and skill indexing."""

    def __init__(
        self,
        db: AsyncSession,
        embedding_svc: EmbeddingService | None = None,
        storage_svc: StorageService | None = None,
    ) -> None:
        self.db = db
        self.parser_utils = PdfParser()
        self.resume_parser = ResumeParserService()
        self.chunker = SemanticChunker(target_token_limit=350, token_overlap=50)
        self.skill_extractor = SkillExtractor()
        self.embedding_svc = embedding_svc or EmbeddingService()
        self.storage_svc = storage_svc or StorageService()

    async def process_and_index_resume(
        self,
        user_id: UUID,
        file_bytes: bytes,
        file_name: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Resume:
        """Processes an uploaded resume through the full intelligence pipeline and persists to DB."""
        ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
        if ext not in ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeException(f"Allowed file formats: {ALLOWED_EXTENSIONS}")

        if len(file_bytes) > MAX_RESUME_SIZE:
            raise FileTooLargeException("Resume file size cannot exceed 15MB")

        # 1. Plain text extraction from binary stream
        raw_text = self.parser_utils.extract_text(file_bytes, ext)
        if not raw_text.strip():
            raw_text = "Empty Resume Document"

        # 2. Section segmenting and text cleaning
        parsed_result = self.resume_parser.parse_resume_text(raw_text)

        # 3. Semantic chunking respecting sentence boundaries
        chunks = self.chunker.chunk_sections(parsed_result.sections)

        # 4. Canonical skill and evidence extraction
        skills = self.skill_extractor.extract_skills(parsed_result.clean_text)

        # 5. Object storage upload
        try:
            s3_key = await self.storage_svc.upload_resume(user_id, file_bytes, file_name)
        except Exception:
            s3_key = f"resumes/{user_id}/local_{file_name}"

        # 6. Generate document-level embedding
        resume_embedding = await self.embedding_svc.embed_text(parsed_result.clean_text[:4000])

        # 7. Create Resume root entity
        resume = Resume(
            user_id=user_id,
            file_name=file_name,
            s3_key=s3_key,
            parsed_text=parsed_result.clean_text,
            embedding=resume_embedding,
            metadata_={
                "word_count": parsed_result.word_count,
                "file_extension": ext,
                "file_size_bytes": len(file_bytes),
                "contact_info": parsed_result.contact_info,
            },
            structured_data={
                "contact_info": parsed_result.contact_info,
                "total_sections": len(parsed_result.sections),
                "total_chunks": len(chunks),
                "total_skills": len(skills),
            },
            parsing_status="completed",
        )
        self.db.add(resume)
        await self.db.flush()
        await self.db.refresh(resume)

        # 8. Persist sections
        section_id_map: dict[str, UUID] = {}
        for sec in parsed_result.sections:
            db_section = ResumeSection(
                resume_id=resume.id,
                section_type=sec.section_type,
                heading=sec.heading,
                content=sec.content,
                sequence_order=sec.sequence_order,
            )
            self.db.add(db_section)
            await self.db.flush()
            section_id_map[sec.heading] = db_section.id

        # 9. Generate chunk embeddings and persist chunks
        chunk_texts = [c.chunk_text for c in chunks]
        chunk_embeddings = await self.embedding_svc.embed_batch(chunk_texts, batch_size=16)

        for i, chunk in enumerate(chunks):
            heading = chunk.metadata.get("section_heading", "")
            sec_id = section_id_map.get(heading)
            emb = chunk_embeddings[i] if i < len(chunk_embeddings) else resume_embedding

            db_chunk = ResumeChunk(
                resume_id=resume.id,
                section_id=sec_id,
                chunk_index=chunk.chunk_index,
                chunk_text=chunk.chunk_text,
                token_count=chunk.token_count,
                embedding=emb,
                metadata_=chunk.metadata,
            )
            self.db.add(db_chunk)

        # 10. Persist candidate skills with evidence attribution
        for sk in skills:
            db_skill = CandidateSkill(
                resume_id=resume.id,
                user_id=user_id,
                skill_name=sk.skill_name,
                normalized_name=sk.normalized_name,
                category=sk.category,
                confidence=sk.confidence,
                years_experience=sk.years_experience,
                proficiency_level=sk.proficiency_level,
                evidence_text=sk.evidence_text,
            )
            self.db.add(db_skill)

        await self.db.flush()
        await self.db.refresh(resume)

        # 11. Audit event
        await record_audit_event(
            db=self.db,
            action="resume.parsed_and_indexed",
            entity_type="resume",
            user_id=user_id,
            entity_id=str(resume.id),
            ip_address=ip_address,
            user_agent=user_agent,
            payload={
                "sections_count": len(parsed_result.sections),
                "chunks_count": len(chunks),
                "skills_count": len(skills),
                "word_count": parsed_result.word_count,
            },
        )

        log.info(
            "resume_intelligence_indexing_complete",
            resume_id=str(resume.id),
            sections=len(parsed_result.sections),
            chunks=len(chunks),
            skills=len(skills),
        )

        return resume

    async def get_resume_detail(self, resume_id: UUID, user_id: UUID) -> Resume:
        """Retrieves full resume hierarchy with sections, chunks, and skills."""
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if resume is None:
            raise NotFoundException("Resume document not found")
        return resume

    async def get_candidate_skills(self, resume_id: UUID, user_id: UUID) -> list[CandidateSkill]:
        """Retrieves extracted skills for a candidate resume."""
        # Ensure user owns resume
        await self.get_resume_detail(resume_id, user_id)

        result = await self.db.execute(
            select(CandidateSkill)
            .where(CandidateSkill.resume_id == resume_id)
            .order_by(CandidateSkill.confidence.desc())
        )
        return list(result.scalars().all())

    async def get_resume_chunks(self, resume_id: UUID, user_id: UUID) -> list[ResumeChunk]:
        """Retrieves semantic chunks for a candidate resume."""
        await self.get_resume_detail(resume_id, user_id)

        result = await self.db.execute(
            select(ResumeChunk)
            .where(ResumeChunk.resume_id == resume_id)
            .order_by(ResumeChunk.chunk_index)
        )
        return list(result.scalars().all())
