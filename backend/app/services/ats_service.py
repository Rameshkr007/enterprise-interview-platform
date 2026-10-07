from __future__ import annotations

import re
from typing import Any
from uuid import UUID

import numpy as np
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    JobDescriptionNotFoundException,
    ResumeNotFoundException,
)
from app.models.ats_analysis import AtsAnalysis, AtsMatchTier, AtsRecommendation
from app.models.job_description import JobDescription
from app.models.resume import CandidateSkill, Resume, ResumeChunk, ResumeSection
from app.services.audit_service import record_audit_event
from app.services.embedding_service import EmbeddingService
from app.services.job_requirement_parser import JobRequirementParser
from app.services.llm_service import LLMService

log = structlog.get_logger(__name__)

# Sibling / Transferable skill relationships for semantic matching
RELATED_SKILLS_MAP: dict[str, list[str]] = {
    "fastapi": ["flask", "django", "express", "nodejs", "rest_api"],
    "django": ["fastapi", "flask", "backend", "python"],
    "react": ["nextjs", "vue", "angular", "frontend"],
    "nextjs": ["react", "frontend", "typescript"],
    "postgresql": ["mysql", "mongodb", "database", "sql", "pgvector"],
    "mysql": ["postgresql", "database", "sql"],
    "redis": ["memcached", "caching", "database"],
    "docker": ["kubernetes", "containerization", "ci_cd", "devops"],
    "kubernetes": ["docker", "devops", "cloud", "aws", "gcp"],
    "aws": ["gcp", "azure", "cloud", "devops"],
    "gcp": ["aws", "azure", "cloud"],
    "langgraph": ["langchain", "rag", "ai_ml", "python"],
    "langchain": ["langgraph", "rag", "ai_ml"],
    "microservices": ["distributed_systems", "system_design", "rest_api", "grpc"],
    "kafka": ["rabbitmq", "websockets", "system_design", "distributed_systems"],
}


class AtsService:
    """Semantic ATS 2.0 Engine with explainable multi-dimensional scoring and evidence validation."""

    def __init__(self, db: AsyncSession, embedding_svc: EmbeddingService | None = None, llm_svc: LLMService | None = None) -> None:
        self.db = db
        self.embedding_svc = embedding_svc or EmbeddingService()
        self.llm_svc = llm_svc or LLMService()
        self.jd_parser = JobRequirementParser()

    async def analyze(self, resume_id: UUID, jd_id: UUID, ip_address: str | None = None, user_agent: str | None = None) -> AtsAnalysis:
        """Executes full multi-dimensional semantic comparison between resume and job description."""
        # Check if already analyzed
        existing = await self.db.execute(
            select(AtsAnalysis).where(AtsAnalysis.resume_id == resume_id, AtsAnalysis.jd_id == jd_id)
        )
        existing_analysis = existing.scalar_one_or_none()
        if existing_analysis is not None:
            return existing_analysis

        resume = await self.db.get(Resume, resume_id)
        if resume is None:
            raise ResumeNotFoundException()

        jd = await self.db.get(JobDescription, jd_id)
        if jd is None:
            raise JobDescriptionNotFoundException()

        # Parse JD requirements if not yet structured
        if not jd.requirements:
            parsed_jd = self.jd_parser.parse_job_description(jd.raw_text, title=jd.title, company=jd.company)
            jd.requirements = [
                {
                    "text": r.requirement_text,
                    "category": r.category,
                    "is_required": r.is_required,
                    "importance": r.importance,
                    "skills": r.skills,
                }
                for r in parsed_jd.requirements
            ]
            jd.structured_skills = parsed_jd.all_skills
            jd.seniority_level = parsed_jd.seniority_level
            jd.min_years_experience = parsed_jd.min_years_experience
            jd.education_required = parsed_jd.education_required
            jd.location_type = parsed_jd.location_type
            self.db.add(jd)
            await self.db.flush()

        # 1. Cosine similarity of document-level embeddings
        cosine_sim = self._calculate_cosine_similarity(resume.embedding, jd.embedding)

        # 2. Extract candidate skills from resume
        skills_res = await self.db.execute(
            select(CandidateSkill).where(CandidateSkill.resume_id == resume_id)
        )
        candidate_skills = list(skills_res.scalars().all())
        candidate_skill_map = {s.normalized_name: s for s in candidate_skills}

        # 3. Match candidate skills against job demands
        match_details, technical_score = self._evaluate_technical_fit(candidate_skill_map, jd.requirements, jd.structured_skills)

        # 4. Evaluate experience & seniority fit
        experience_score, seniority_fit = self._evaluate_experience_fit(candidate_skills, resume.parsed_text, jd.min_years_experience, jd.seniority_level)

        # 5. Evaluate education & project relevance
        education_score = self._evaluate_education_fit(resume.parsed_text, jd.education_required)
        project_score = self._evaluate_project_fit(resume.parsed_text, jd.structured_skills)

        # 6. Composite overall score & tier
        # Technical (40%), Semantic Similarity (25%), Experience (15%), Projects (10%), Education (10%)
        overall_score = (
            technical_score * 0.40
            + (cosine_sim * 100) * 0.25
            + experience_score * 0.15
            + project_score * 0.10
            + education_score * 0.10
        )
        overall_score = min(max(round(overall_score, 1), 0.0), 100.0)

        match_tier = self._score_to_tier(overall_score)
        recommendation = self._determine_recommendation(overall_score, match_details)

        # 7. Synthesize explainable summary
        summary = self._generate_explainable_summary(
            candidate_name=resume.metadata_.get("contact_info", {}).get("candidate_name", "The candidate"),
            job_title=jd.title,
            company=jd.company,
            overall_score=overall_score,
            recommendation=recommendation,
            match_details=match_details,
            seniority_fit=seniority_fit,
        )

        matched_skills_list = [
            {"skill_name": m["skill_name"], "match_type": m["match_type"], "evidence": m["resume_evidence"], "confidence": m["confidence"]}
            for m in match_details if m["match_type"] in ("explicit_match", "semantic_match", "partial_match")
        ]
        skill_gaps_list = [
            {"skill_name": m["skill_name"], "match_type": m["match_type"], "is_required": m["is_required"], "suggested_action": m["suggested_action"]}
            for m in match_details if m["match_type"] in ("missing_skill", "unknown")
        ]

        section_scores = {
            "technical": round(technical_score, 1),
            "semantic": round(cosine_sim * 100, 1),
            "experience": round(experience_score, 1),
            "projects": round(project_score, 1),
            "education": round(education_score, 1),
        }

        analysis = AtsAnalysis(
            resume_id=resume_id,
            jd_id=jd_id,
            cosine_similarity=cosine_sim,
            match_tier=match_tier,
            recommendation=recommendation.value,
            technical_score=technical_score,
            experience_score=experience_score,
            education_score=education_score,
            project_score=project_score,
            seniority_fit=seniority_fit,
            skill_gaps=skill_gaps_list,
            matched_skills=matched_skills_list,
            skill_gap_details=match_details,
            section_scores=section_scores,
            overall_score=overall_score,
            explainable_summary=summary,
        )
        self.db.add(analysis)
        await self.db.flush()
        await self.db.refresh(analysis)

        # Record audit log
        await record_audit_event(
            db=self.db,
            action="ats.analysis_completed",
            entity_type="ats_analysis",
            user_id=resume.user_id,
            entity_id=str(analysis.id),
            ip_address=ip_address,
            user_agent=user_agent,
            payload={
                "overall_score": overall_score,
                "tier": match_tier.value,
                "recommendation": recommendation.value,
            },
        )

        log.info(
            "ats_analysis_complete",
            analysis_id=str(analysis.id),
            overall_score=overall_score,
            recommendation=recommendation.value,
        )

        return analysis

    async def compare_multiple_jobs(
        self, resume_id: UUID, jd_ids: list[UUID]
    ) -> list[AtsAnalysis]:
        """Runs batch evaluation of a single candidate resume against multiple target jobs."""
        results: list[AtsAnalysis] = []
        for j_id in jd_ids:
            res = await self.analyze(resume_id, j_id)
            results.append(res)
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results

    def _calculate_cosine_similarity(self, v1: list[float] | None, v2: list[float] | None) -> float:
        if not v1 or not v2:
            return 0.5
        arr1 = np.array(v1, dtype=float)
        arr2 = np.array(v2, dtype=float)
        norm = float(np.linalg.norm(arr1) * np.linalg.norm(arr2))
        raw = float(np.dot(arr1, arr2) / norm) if norm > 0 else 0.5
        scaled = (raw + 1.0) / 2.0
        return float(max(0.0, min(1.0, scaled)))

    def _evaluate_technical_fit(
        self,
        candidate_skills: dict[str, CandidateSkill],
        requirements: list[dict],
        structured_skills: list[str],
    ) -> tuple[list[dict], float]:
        """Classifies each demanded skill into explicit, semantic, partial, or missing match."""
        details: list[dict] = []
        required_weights = 0.0
        earned_weights = 0.0

        all_needed_skills = set(structured_skills)
        for req in requirements:
            for s in req.get("skills", []):
                all_needed_skills.add(s)

        if not all_needed_skills:
            for req in requirements:
                words = re.findall(r"\b[A-Z][a-zA-Z0-9#+]+\b", req.get("text", ""))
                for w in words:
                    if len(w) > 2 and w.lower() not in ("the", "and", "for", "with", "from", "role", "team", "about", "join"):
                        all_needed_skills.add(w)

        if not all_needed_skills:
            return [], 20.0

        for skill_name in all_needed_skills:
            norm_key = re.sub(r"[^a-z0-9]", "", skill_name.lower())
            is_required = any(
                skill_name in r.get("skills", []) and r.get("is_required", True) for r in requirements
            )
            weight = 1.5 if is_required else 1.0
            required_weights += weight

            # 1. Check Explicit Match
            matched_candidate_skill = None
            for cand_key, cand_skill in candidate_skills.items():
                if cand_key == norm_key or cand_skill.skill_name.lower() == skill_name.lower():
                    matched_candidate_skill = cand_skill
                    break

            if matched_candidate_skill:
                earned_weights += weight * 1.0
                details.append({
                    "skill_name": skill_name,
                    "match_type": "explicit_match",
                    "is_required": is_required,
                    "confidence": matched_candidate_skill.confidence,
                    "resume_evidence": matched_candidate_skill.evidence_text,
                    "suggested_action": "Strong direct qualification. Highlight relevant achievements in interview.",
                })
                continue

            # 2. Check Semantic / Related Skill Match
            related_keys = RELATED_SKILLS_MAP.get(norm_key, [])
            found_related = None
            for rk in related_keys:
                if rk in candidate_skills:
                    found_related = candidate_skills[rk]
                    break

            if found_related:
                earned_weights += weight * 0.75
                details.append({
                    "skill_name": skill_name,
                    "match_type": "semantic_match",
                    "is_required": is_required,
                    "confidence": 0.85,
                    "resume_evidence": f"Demonstrated proficiency in sibling technology '{found_related.skill_name}': {found_related.evidence_text[:120]}",
                    "suggested_action": f"Prepare to discuss technology transferability from {found_related.skill_name} to {skill_name}.",
                })
                continue

            # 3. Missing Skill
            details.append({
                "skill_name": skill_name,
                "match_type": "missing_skill" if is_required else "partial_match",
                "is_required": is_required,
                "confidence": 0.0,
                "resume_evidence": "Not found in candidate resume.",
                "suggested_action": f"Acquire core foundational experience in {skill_name} or complete hands-on project.",
            })

        technical_score = (earned_weights / required_weights * 100) if required_weights > 0 else 75.0
        return details, min(round(technical_score, 1), 100.0)

    def _evaluate_experience_fit(
        self,
        candidate_skills: list[CandidateSkill],
        resume_text: str,
        min_years: float | None,
        job_seniority: str,
    ) -> tuple[float, str]:
        """Calculates experience fit and seniority alignment."""
        job_min = min_years if min_years is not None and min_years > 0 else 2.0

        # Calculate max experience years found in skills or text
        years_found = [s.years_experience for s in candidate_skills if s.years_experience]
        # Also parse from text
        text_years = re.findall(r"(\d+(?:\.\d+)?)\+?\s*years?", resume_text, re.IGNORECASE)
        for y in text_years:
            try:
                years_found.append(float(y))
            except ValueError:
                pass

        candidate_years = max(years_found) if years_found else 3.0

        # Ratio of candidate years to job minimum
        ratio = candidate_years / job_min
        if ratio >= 1.5:
            score = 100.0
            seniority_fit = "highly_qualified" if job_seniority in ("senior", "staff", "lead") else "potential_overqualification"
        elif ratio >= 1.0:
            score = 90.0
            seniority_fit = "matching"
        elif ratio >= 0.7:
            score = 75.0
            seniority_fit = "stretch_growth"
        else:
            score = 50.0
            seniority_fit = "underqualified"

        return score, seniority_fit

    def _evaluate_education_fit(self, resume_text: str, education_required: str | None) -> float:
        t_lower = resume_text.lower()
        if "ph.d" in t_lower or "phd" in t_lower:
            return 100.0
        if "master" in t_lower or "m.s." in t_lower:
            return 95.0
        if "bachelor" in t_lower or "b.s." in t_lower or "computer science" in t_lower:
            return 90.0
        return 75.0

    def _evaluate_project_fit(self, resume_text: str, needed_skills: list[str]) -> float:
        t_lower = resume_text.lower()
        matched = 0
        for s in needed_skills:
            if s.lower() in t_lower:
                matched += 1
        ratio = matched / len(needed_skills) if needed_skills else 1.0
        return min(round(ratio * 100, 1), 100.0)

    def _score_to_tier(self, score: float) -> AtsMatchTier:
        if score >= 85.0:
            return AtsMatchTier.excellent
        if score >= 70.0:
            return AtsMatchTier.good
        if score >= 50.0:
            return AtsMatchTier.fair
        return AtsMatchTier.poor

    def _determine_recommendation(self, score: float, match_details: list[dict]) -> AtsRecommendation:
        missing_required = any(m["match_type"] == "missing_skill" and m["is_required"] for m in match_details)
        if score >= 75.0 and not missing_required:
            return AtsRecommendation.apply
        if score >= 50.0:
            return AtsRecommendation.improve_then_apply
        return AtsRecommendation.low_priority

    def _generate_explainable_summary(
        self,
        candidate_name: str,
        job_title: str,
        company: str | None,
        overall_score: float,
        recommendation: AtsRecommendation,
        match_details: list[dict],
        seniority_fit: str,
    ) -> str:
        explicit_matches = [m["skill_name"] for m in match_details if m["match_type"] == "explicit_match"]
        semantic_matches = [m["skill_name"] for m in match_details if m["match_type"] == "semantic_match"]
        missing_req = [m["skill_name"] for m in match_details if m["match_type"] == "missing_skill" and m["is_required"]]

        target = f"{job_title}" + (f" at {company}" if company else "")
        summary_lines = [
            f"Candidate profile achieves an ATS Compatibility Score of {overall_score}/100 for {target}.",
            f"Verdict: {recommendation.value} (Seniority Alignment: {seniority_fit.replace('_', ' ').title()}).",
        ]

        if explicit_matches:
            summary_lines.append(f"Strong explicit skills verified with resume evidence: {', '.join(explicit_matches[:6])}.")
        if semantic_matches:
            summary_lines.append(f"Complementary transferable qualifications detected: {', '.join(semantic_matches[:4])}.")
        if missing_req:
            summary_lines.append(f"High-priority qualifications to address: {', '.join(missing_req[:4])}.")
        else:
            summary_lines.append("All primary technical prerequisites are satisfied with verifiable evidence.")

        return " ".join(summary_lines)
