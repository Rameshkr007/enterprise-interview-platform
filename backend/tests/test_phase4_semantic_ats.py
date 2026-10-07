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
from app.models.ats_analysis import AtsAnalysis
from app.models.job_description import JobDescription
from app.models.resume import Resume
from app.services.job_requirement_parser import JobRequirementParser


SAMPLE_RESUME_TEXT = """
Sarah Jenkins
Email: sarah.jenkins@example.com
Phone: (555) 234-5678
LinkedIn: linkedin.com/in/sarahjenkins-dev
GitHub: github.com/sarahjenkins

PROFESSIONAL SUMMARY
Staff Full-Stack AI Engineer with 6+ years of experience building high-scale distributed backend architectures and agentic AI platforms. Expert in Python, FastAPI, React, and PostgreSQL.

WORK EXPERIENCE
Staff AI Platform Engineer | TechCorp Global | 2022 - Present
- Architected enterprise LLM and LangGraph workflow pipelines using FastAPI, Redis, and PostgreSQL with PGVector.
- Designed distributed event-driven microservices processing 50M+ events daily with Apache Kafka and Docker.
- Orchestrated Kubernetes deployments across AWS EKS, improving system availability to 99.99%.
- Spearheaded CI/CD pipelines with GitHub Actions.

TECHNICAL SKILLS
- Languages: Python, TypeScript, JavaScript, SQL, Go (Golang)
- Backend: FastAPI, Node.js, RESTful APIs, gRPC, Microservices
- Databases: PostgreSQL, Redis, PGVector, MongoDB
- Cloud & DevOps: AWS, Docker, Kubernetes, Terraform, CI/CD, Linux
- AI & ML: LangChain, LangGraph, Machine Learning, Deep Learning, RAG
- Architecture: Distributed Systems, System Design, Apache Kafka, WebSockets

EDUCATION
Bachelor of Science in Computer Science | UC Berkeley | 2015 - 2019
"""

SAMPLE_MATCHING_JD = """
About the Role:
We are seeking a Senior Distributed Systems & AI Engineer to lead the architectural evolution of our global intelligence engine. 

Key Responsibilities:
- Design, scale, and maintain high-throughput distributed microservices handling real-time data streaming.
- Build production-ready Agentic AI workflows and LLM orchestration systems with Python and FastAPI.
- Deploy and manage containerized services on Kubernetes clusters running in AWS.
- Collaborate on database design, caching strategies, and vector search with PostgreSQL and Redis.

Minimum Qualifications:
- 5+ years of professional backend engineering experience with Python and microservices architecture.
- Demonstrated production experience with FastAPI, Docker, and Kubernetes.
- Deep hands-on proficiency with relational databases (PostgreSQL) and caching (Redis).
- Proven track record with distributed event streaming platforms (Apache Kafka).
- Bachelor's degree in Computer Science or equivalent practical experience.

Preferred Qualifications:
- Experience with Agentic AI frameworks such as LangGraph or LangChain is a major plus.
- Experience with cloud-native AWS services and Infrastructure as Code (Terraform).
- Familiarity with TypeScript and modern React applications.
"""

SAMPLE_NON_MATCHING_JD = """
Senior iOS Swift Developer
About the Role:
Join our mobile team to develop native iOS consumer applications with delightful animations and fluid touch interactions.

Requirements:
- 5+ years of native iOS application development with Swift, SwiftUI, and UIKit.
- Deep expertise in CoreData, Combine, and Apple App Store deployment pipelines.
- Experience with Objective-C legacy codebases.
- Strong knowledge of Apple Human Interface Guidelines.
"""


async def test_job_requirement_parser():
    print("--- 1. Testing JobRequirementParser Logic ---")
    parser = JobRequirementParser()
    parsed = parser.parse_job_description(SAMPLE_MATCHING_JD, title="Senior Distributed Systems & AI Engineer", company="Apex AI")

    assert parsed.seniority_level == "senior"
    assert parsed.min_years_experience >= 4.0
    assert "Bachelor" in parsed.education_required
    assert len(parsed.requirements) >= 5

    skills_detected = {s.lower() for s in parsed.all_skills}
    for expected in ["python", "fastapi", "docker", "kubernetes", "postgresql", "redis", "apache kafka"]:
        assert any(expected in s for s in skills_detected), f"Expected skill '{expected}' not detected in JD requirements"
    print(f"[PASS] JobRequirementParser extracted {len(parsed.requirements)} requirements and {len(parsed.all_skills)} target skills.")


async def test_api_ats_analysis():
    print("--- 2. Testing Semantic ATS 2.0 API & Multi-Job Match ---")
    transport = ASGITransport(app=app)
    suffix = uuid4().hex[:8]
    test_headers = {"X-Forwarded-For": f"192.168.4.{int(suffix[:2], 16)}"}
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", headers=test_headers) as client:
        # Register user
        user_email = f"candidate_{suffix}@atsplatform.ai"
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

        # 1. Upload Resume
        files = {
            "file": ("sarah_jenkins_resume.txt", SAMPLE_RESUME_TEXT.encode("utf-8"), "text/plain")
        }
        resume_res = await client.post("/api/v1/resumes/upload", headers=auth_headers, files=files)
        assert resume_res.status_code == 201
        resume_id = resume_res.json()["resume_id"]
        print(f"[PASS] Candidate resume uploaded and indexed. ID: {resume_id}")

        # 2. Create Matching JD
        jd1_res = await client.post(
            "/api/v1/ats/job-description",
            headers=auth_headers,
            json={
                "title": "Senior Distributed Systems & AI Engineer",
                "company": "Apex AI Global",
                "raw_text": SAMPLE_MATCHING_JD,
            },
        )
        assert jd1_res.status_code == 201
        jd1_id = jd1_res.json()["jd_id"]
        print(f"[PASS] Matching Job Description created. ID: {jd1_id}")

        # 3. Create Non-Matching JD
        jd2_res = await client.post(
            "/api/v1/ats/job-description",
            headers=auth_headers,
            json={
                "title": "Senior iOS Swift Developer",
                "company": "MobileLab Inc",
                "raw_text": SAMPLE_NON_MATCHING_JD,
            },
        )
        assert jd2_res.status_code == 201
        jd2_id = jd2_res.json()["jd_id"]
        print(f"[PASS] Non-Matching Job Description created. ID: {jd2_id}")

        # 4. Analyze Resume against Matching JD
        analyze_res = await client.post(
            "/api/v1/ats/analyze",
            headers=auth_headers,
            json={"resume_id": resume_id, "jd_id": jd1_id},
        )
        assert analyze_res.status_code == 200, f"Analysis failed: {analyze_res.text}"
        analysis_data = analyze_res.json()
        assert analysis_data["overall_score"] >= 75.0, f"Expected overall score >= 75.0, got {analysis_data['overall_score']}"
        assert analysis_data["recommendation"] == "APPLY"
        assert analysis_data["match_tier"] in ("good", "excellent")
        assert analysis_data["technical_score"] >= 75.0
        assert analysis_data["seniority_fit"] in ("matching", "highly_qualified")
        assert len(analysis_data["matched_skills"]) > 0
        assert len(analysis_data["explainable_summary"]) > 50

        # Verify explicit evidence exists in matched skills
        explicit_matches = [m for m in analysis_data["matched_skills"] if m.get("match_type") == "explicit_match"]
        assert len(explicit_matches) >= 3, "Expected at least 3 explicit evidence-backed skill matches"
        assert len(explicit_matches[0]["evidence"]) > 10
        print(f"[PASS] ATS 2.0 Analysis validated: Score={analysis_data['overall_score']}/100, Recommendation={analysis_data['recommendation']}, Explicit Matches={len(explicit_matches)}.")

        # 5. Multi-Job Match Intelligence
        multi_res = await client.post(
            "/api/v1/ats/multi-match",
            headers=auth_headers,
            json={"resume_id": resume_id, "jd_ids": [jd1_id, jd2_id]},
        )
        assert multi_res.status_code == 200
        ranked_jobs = multi_res.json()
        assert len(ranked_jobs) == 2
        # Highest match must be Apex AI (Matching JD)
        assert ranked_jobs[0]["jd_id"] == jd1_id
        assert ranked_jobs[0]["recommendation"] == "APPLY"
        assert ranked_jobs[1]["jd_id"] == jd2_id
        assert ranked_jobs[1]["overall_score"] < ranked_jobs[0]["overall_score"]
        print(f"[PASS] Multi-Job Match ranked #{1}: {ranked_jobs[0]['title']} ({ranked_jobs[0]['overall_score']}) > #{2}: {ranked_jobs[1]['title']} ({ranked_jobs[1]['overall_score']}).")

        # 6. Verify Audit Log
        async with AsyncSessionLocal() as session:
            stmt = select(AuditLog).where(
                AuditLog.action == "ats.analysis_completed",
                AuditLog.entity_id == str(analysis_data["id"]),
            )
            audit_entry = (await session.execute(stmt)).scalar_one_or_none()
            assert audit_entry is not None, "Audit log for ATS analysis was not found"
        print("[PASS] Audit log verified for ATS analysis completion.")


async def run_all():
    print("=== RUNNING PHASE 4 SEMANTIC ATS 2.0 & JOB MATCH TESTS ===")
    await test_job_requirement_parser()
    await test_api_ats_analysis()
    await close_redis_pool()
    print("=== ALL PHASE 4 SEMANTIC ATS 2.0 TESTS PASSED ===")


if __name__ == "__main__":
    asyncio.run(run_all())
