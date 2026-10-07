import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import asyncio
from uuid import uuid4
import httpx
from httpx import ASGITransport
from sqlalchemy import select

from app.database import AsyncSessionLocal, check_database_health
from app.core.redis import check_redis_health, close_redis_pool
from app.main import app
from app.models.audit_log import AuditLog
from app.models.resume import Resume, ResumeSection, ResumeChunk, CandidateSkill
from app.services.resume_parser_service import ResumeParserService
from app.services.semantic_chunker import SemanticChunker
from app.services.skill_extractor import SkillExtractor


SAMPLE_RESUME_TEXT = """
Sarah Jenkins
Email: sarah.jenkins@example.com
Phone: (555) 234-5678
LinkedIn: linkedin.com/in/sarahjenkins-dev
GitHub: github.com/sarahjenkins

PROFESSIONAL SUMMARY
Senior Full-Stack AI Engineer with 6+ years of production experience architecting high-scale distributed systems and AI platforms. Expert in Python, FastAPI, React, and PostgreSQL. Proven track record leading cross-functional engineering teams and scaling microservices infrastructure to handle millions of daily requests.

WORK EXPERIENCE
Staff AI Platform Engineer | TechCorp Global | 2022 - Present
- Architected enterprise LLM and LangGraph agent workflow pipelines using FastAPI, Redis, and PostgreSQL with PGVector.
- Designed distributed event-driven microservices processing 50M+ events daily with Apache Kafka and Docker containerization.
- Orchestrated Kubernetes deployments across AWS EKS, improving system availability to 99.99%.
- Spearheaded CI/CD pipelines with GitHub Actions, reducing release cycle time by 45%.

Senior Software Engineer | CloudScale Inc | 2019 - 2022
- Built real-time streaming analytics dashboards using React, Next.js, TypeScript, and WebSockets.
- Migrated legacy monolith into scalable RESTful APIs and gRPC microservices using Python and Docker.
- Optimized PostgreSQL database queries and indexes, decreasing 95th percentile latency from 650ms to 45ms.
- Mentored 6 junior engineers through code reviews, design docs, and architectural sparring.

TECHNICAL SKILLS
- Programming Languages: Python, TypeScript, JavaScript, SQL, Go (Golang)
- Frontend: React, Next.js, TailwindCSS, Redux, HTML5 / CSS3
- Backend & Frameworks: FastAPI, Node.js, Express, RESTful APIs, gRPC
- Databases & Storage: PostgreSQL, Redis, MongoDB, PGVector
- Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD, Linux
- AI & ML: LangChain, LangGraph, Machine Learning, Deep Learning, RAG, NLP
- Architecture: Microservices, Distributed Systems, System Design, Apache Kafka, WebSockets

EDUCATION
Bachelor of Science in Computer Science
University of California, Berkeley | 2015 - 2019
GPA: 3.85 / 4.0

PROJECTS
Autonomous Agent Evaluator
- Developed end-to-end multi-agent evaluation platform using LangGraph, Python, and PyTorch.
- Incorporated vector similarity search using PGVector and text-embedding-3-large models.

CERTIFICATIONS
- AWS Certified Solutions Architect - Professional
- Certified Kubernetes Administrator (CKA)
"""


async def test_unit_services():
    print("--- 1. Testing ResumeParserService Unit Logic ---")
    parser = ResumeParserService()
    parsed = parser.parse_resume_text(SAMPLE_RESUME_TEXT)

    assert parsed.word_count > 150
    assert parsed.contact_info.get("email") == "sarah.jenkins@example.com"
    assert parsed.contact_info.get("phone") == "(555) 234-5678"
    assert "github.com/sarahjenkins" in parsed.contact_info.get("github", "")
    assert len(parsed.sections) >= 5, f"Expected at least 5 sections, got {len(parsed.sections)}"

    section_types = [s.section_type for s in parsed.sections]
    assert "summary" in section_types
    assert "experience" in section_types
    assert "skills" in section_types
    assert "education" in section_types
    assert "projects" in section_types
    print(f"[PASS] Section parser identified {len(parsed.sections)} sections: {section_types}")

    print("--- 2. Testing SemanticChunker Unit Logic ---")
    chunker = SemanticChunker(target_token_limit=150, token_overlap=30)
    chunks = chunker.chunk_sections(parsed.sections)
    assert len(chunks) >= len(parsed.sections)
    for c in chunks:
        assert c.chunk_text.startswith("[")  # Verify contextual section prefix
        assert c.token_count > 0
        assert c.section_type != ""
    print(f"[PASS] Semantic chunker produced {len(chunks)} contextual chunks with section prefixes.")

    print("--- 3. Testing SkillExtractor Unit Logic ---")
    extractor = SkillExtractor()
    skills = extractor.extract_skills(SAMPLE_RESUME_TEXT)
    assert len(skills) >= 15, f"Expected at least 15 skills, got {len(skills)}"

    normalized_names = {s.normalized_name for s in skills}
    expected_skills = {"python", "fastapi", "react", "postgresql", "docker", "kubernetes", "aws", "langgraph", "redis"}
    for exp in expected_skills:
        assert exp in normalized_names, f"Expected skill '{exp}' not detected"

    # Check evidence attribution
    py_skill = next(s for s in skills if s.normalized_name == "python")
    assert len(py_skill.evidence_text) > 10
    assert py_skill.confidence >= 0.8
    assert py_skill.category == "language"
    print(f"[PASS] Skill extractor identified {len(skills)} skills with normalized names and verbatim evidence.")


async def test_api_integration():
    print("--- 4. Testing End-to-End API Integration & DB Persistence ---")
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        # Register user
        suffix = uuid4().hex[:8]
        user_email = f"candidate_{suffix}@testresume.com"
        user_pwd = "SecurePassword123!"

        await client.post(
            "/api/v1/auth/register",
            json={"email": user_email, "full_name": "Sarah Jenkins", "password": user_pwd},
        )
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"email": user_email, "password": user_pwd},
        )
        token = login_res.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {token}"}

        # Upload resume as text file
        files = {
            "file": ("sarah_jenkins_resume.txt", SAMPLE_RESUME_TEXT.encode("utf-8"), "text/plain")
        }
        upload_res = await client.post(
            "/api/v1/resumes/upload",
            headers=auth_headers,
            files=files,
        )
        assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
        upload_data = upload_res.json()
        resume_id = upload_data["resume_id"]
        assert upload_data["section_count"] >= 5
        assert upload_data["chunk_count"] >= 5
        assert upload_data["skill_count"] >= 15
        assert upload_data["status"] == "completed"
        print(f"[PASS] Upload endpoint succeeded. Resume ID: {resume_id}, Sections: {upload_data['section_count']}, Chunks: {upload_data['chunk_count']}, Skills: {upload_data['skill_count']}.")

        # Retrieve full detail
        detail_res = await client.get(f"/api/v1/resumes/{resume_id}", headers=auth_headers)
        assert detail_res.status_code == 200, f"Get detail failed: {detail_res.text}"
        detail_data = detail_res.json()
        assert len(detail_data["sections"]) == upload_data["section_count"]
        assert len(detail_data["chunks"]) == upload_data["chunk_count"]
        assert len(detail_data["skills"]) == upload_data["skill_count"]
        print("[PASS] Full resume detail retrieved with verified section, chunk, and skill counts.")

        # Retrieve skills profile
        skills_res = await client.get(f"/api/v1/resumes/{resume_id}/skills", headers=auth_headers)
        assert skills_res.status_code == 200
        skills_data = skills_res.json()
        assert skills_data["total_skills"] == upload_data["skill_count"]
        assert len(skills_data["top_skills"]) > 0
        assert "backend" in skills_data["skills_by_category"]
        assert "language" in skills_data["skills_by_category"]
        print(f"[PASS] Skill profile retrieved with {len(skills_data['skills_by_category'])} category groups.")

        # Retrieve chunks
        chunks_res = await client.get(f"/api/v1/resumes/{resume_id}/chunks", headers=auth_headers)
        assert chunks_res.status_code == 200
        chunks_data = chunks_res.json()
        assert len(chunks_data) == upload_data["chunk_count"]
        assert all(c["token_count"] > 0 for c in chunks_data)
        print(f"[PASS] Resume chunks retrieved with valid token counts and metadata.")

        # List user's resumes
        list_res = await client.get("/api/v1/resumes/me", headers=auth_headers)
        assert list_res.status_code == 200
        user_resumes = list_res.json()
        assert any(r["resume_id"] == resume_id for r in user_resumes)
        print("[PASS] /resumes/me endpoint returned uploaded resume in candidate portfolio.")

        # Verify audit log recorded
        async with AsyncSessionLocal() as session:
            stmt = select(AuditLog).where(
                AuditLog.action == "resume.parsed_and_indexed",
                AuditLog.entity_id == str(resume_id),
            )
            audit_entry = (await session.execute(stmt)).scalar_one_or_none()
            assert audit_entry is not None, "Audit log for resume indexing was not found"
        print("[PASS] Audit log verified for resume indexing event.")


async def run_all():
    print("=== RUNNING PHASE 3 RESUME INTELLIGENCE & CHUNKING TESTS ===")
    await test_unit_services()
    await test_api_integration()
    await close_redis_pool()
    print("=== ALL PHASE 3 RESUME INTELLIGENCE TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_all())
