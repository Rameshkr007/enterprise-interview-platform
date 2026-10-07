from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class ExtractedSkill:
    skill_name: str
    normalized_name: str
    category: str
    confidence: float
    years_experience: float | None
    proficiency_level: str
    evidence_text: str


class SkillExtractor:
    """Enterprise skill taxonomy matching and semantic evidence extraction."""

    # Canonical taxonomy with normalized key, display name, category, and alias patterns
    TAXONOMY: dict[str, dict[str, Any]] = {
        # ── Languages ─────────────────────────────────────────────────────────
        "python": {"name": "Python", "category": "language", "aliases": [r"\bpython(?:3)?\b"]},
        "typescript": {"name": "TypeScript", "category": "language", "aliases": [r"\btypescript\b", r"\bts\b"]},
        "javascript": {"name": "JavaScript", "category": "language", "aliases": [r"\bjavascript\b", r"\bjs\b"]},
        "golang": {"name": "Go (Golang)", "category": "language", "aliases": [r"\bgolang\b", r"\bgo\s+language\b"]},
        "rust": {"name": "Rust", "category": "language", "aliases": [r"\brust\b"]},
        "java": {"name": "Java", "category": "language", "aliases": [r"\bjava\b(?!\s*script)"]},
        "cpp": {"name": "C++", "category": "language", "aliases": [r"\bc\+\+\b"]},
        "sql": {"name": "SQL", "category": "language", "aliases": [r"\bsql\b"]},
        "swift": {"name": "Swift", "category": "language", "aliases": [r"\bswift\b"]},
        "kotlin": {"name": "Kotlin", "category": "language", "aliases": [r"\bkotlin\b"]},
        "objectivec": {"name": "Objective-C", "category": "language", "aliases": [r"\bobjective[\s-]c\b"]},
        # ── Mobile ────────────────────────────────────────────────────────────
        "ios": {"name": "iOS", "category": "mobile", "aliases": [r"\bios\b", r"\bapple\s+ios\b"]},
        "swiftui": {"name": "SwiftUI", "category": "mobile", "aliases": [r"\bswiftui\b"]},
        "uikit": {"name": "UIKit", "category": "mobile", "aliases": [r"\buikit\b"]},
        "android": {"name": "Android", "category": "mobile", "aliases": [r"\bandroid\b"]},
        "flutter": {"name": "Flutter", "category": "mobile", "aliases": [r"\bflutter\b"]},
        # ── Frontend ──────────────────────────────────────────────────────────
        "react": {"name": "React", "category": "frontend", "aliases": [r"\breact(?:\.js|js)?\b"]},
        "nextjs": {"name": "Next.js", "category": "frontend", "aliases": [r"\bnext(?:\.js|js)?\b"]},
        "vue": {"name": "Vue.js", "category": "frontend", "aliases": [r"\bvue(?:\.js|js)?\b"]},
        "angular": {"name": "Angular", "category": "frontend", "aliases": [r"\bangular(?:\.js|js)?\b"]},
        "tailwind": {"name": "TailwindCSS", "category": "frontend", "aliases": [r"\btailwind(?:css)?\b"]},
        "redux": {"name": "Redux", "category": "frontend", "aliases": [r"\bredux\b"]},
        "html_css": {"name": "HTML5 / CSS3", "category": "frontend", "aliases": [r"\bhtml5?\b", r"\bcss3?\b"]},
        # ── Backend ───────────────────────────────────────────────────────────
        "fastapi": {"name": "FastAPI", "category": "backend", "aliases": [r"\bfastapi\b"]},
        "django": {"name": "Django", "category": "backend", "aliases": [r"\bdjango\b"]},
        "flask": {"name": "Flask", "category": "backend", "aliases": [r"\bflask\b"]},
        "nodejs": {"name": "Node.js", "category": "backend", "aliases": [r"\bnode(?:\.js|js)?\b"]},
        "express": {"name": "Express.js", "category": "backend", "aliases": [r"\bexpress(?:\.js|js)?\b"]},
        "graphql": {"name": "GraphQL", "category": "backend", "aliases": [r"\bgraphql\b"]},
        "rest_api": {"name": "RESTful APIs", "category": "backend", "aliases": [r"\brest(?:ful)?\s+apis?\b", r"\brest\s+architecture\b"]},
        "grpc": {"name": "gRPC", "category": "backend", "aliases": [r"\bgrpc\b"]},
        # ── Databases & Caching ───────────────────────────────────────────────
        "postgresql": {"name": "PostgreSQL", "category": "database", "aliases": [r"\bpostgres(?:ql)?\b"]},
        "redis": {"name": "Redis", "category": "database", "aliases": [r"\bredis\b"]},
        "mongodb": {"name": "MongoDB", "category": "database", "aliases": [r"\bmongo(?:db)?\b"]},
        "elasticsearch": {"name": "Elasticsearch", "category": "database", "aliases": [r"\belasticsearch\b", r"\belastic\s+search\b"]},
        "pgvector": {"name": "PGVector", "category": "database", "aliases": [r"\bpgvector\b", r"\bvector\s+database\b"]},
        # ── Cloud & DevOps ────────────────────────────────────────────────────
        "docker": {"name": "Docker", "category": "devops", "aliases": [r"\bdocker\b", r"\bcontainerization\b"]},
        "kubernetes": {"name": "Kubernetes", "category": "devops", "aliases": [r"\bkubernetes\b", r"\bk8s\b"]},
        "aws": {"name": "AWS", "category": "cloud", "aliases": [r"\baws\b", r"\bamazon\s+web\s+services\b"]},
        "gcp": {"name": "Google Cloud (GCP)", "category": "cloud", "aliases": [r"\bgcp\b", r"\bgoogle\s+cloud\b"]},
        "azure": {"name": "Microsoft Azure", "category": "cloud", "aliases": [r"\bazure\b"]},
        "terraform": {"name": "Terraform", "category": "devops", "aliases": [r"\bterraform\b", r"\biac\b"]},
        "ci_cd": {"name": "CI/CD Pipelines", "category": "devops", "aliases": [r"\bci\/cd\b", r"\bgithub\s+actions\b", r"\bjenkins\b"]},
        "linux": {"name": "Linux", "category": "devops", "aliases": [r"\blinux\b", r"\bunix\b"]},
        # ── AI, ML & GenAI ────────────────────────────────────────────────────
        "langchain": {"name": "LangChain", "category": "ai_ml", "aliases": [r"\blangchain\b"]},
        "langgraph": {"name": "LangGraph", "category": "ai_ml", "aliases": [r"\blanggraph\b"]},
        "pytorch": {"name": "PyTorch", "category": "ai_ml", "aliases": [r"\bpytorch\b"]},
        "tensorflow": {"name": "TensorFlow", "category": "ai_ml", "aliases": [r"\btensorflow\b"]},
        "machine_learning": {"name": "Machine Learning", "category": "ai_ml", "aliases": [r"\bmachine\s+learning\b", r"\bml\b"]},
        "deep_learning": {"name": "Deep Learning", "category": "ai_ml", "aliases": [r"\bdeep\s+learning\b"]},
        "nlp": {"name": "Natural Language Processing (NLP)", "category": "ai_ml", "aliases": [r"\bnlp\b", r"\bnatural\s+language\s+processing\b"]},
        "rag": {"name": "Retrieval-Augmented Generation (RAG)", "category": "ai_ml", "aliases": [r"\brag\b", r"\bretrieval[\s-]augmented\b"]},
        # ── Architecture & Systems ────────────────────────────────────────────
        "system_design": {"name": "System Design", "category": "system_design", "aliases": [r"\bsystem\s+design\b", r"\bsoftware\s+architecture\b"]},
        "microservices": {"name": "Microservices", "category": "system_design", "aliases": [r"\bmicroservices\b", r"\bmicroservice\s+architecture\b"]},
        "distributed_systems": {"name": "Distributed Systems", "category": "system_design", "aliases": [r"\bdistributed\s+systems\b"]},
        "kafka": {"name": "Apache Kafka", "category": "system_design", "aliases": [r"\bkafka\b", r"\bevent-driven\b"]},
        "websockets": {"name": "WebSockets", "category": "system_design", "aliases": [r"\bwebsockets?\b", r"\brealtime\s+streaming\b"]},
    }

    def extract_skills(self, text: str) -> list[ExtractedSkill]:
        """Scans resume text, identifies matching skills, and extracts exact sentences as evidence."""
        extracted: list[ExtractedSkill] = []
        sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", text) if s.strip()]

        for norm_key, info in self.TAXONOMY.items():
            best_match: str | None = None
            evidence_snippet: str = ""

            for alias_pat in info["aliases"]:
                pattern = re.compile(alias_pat, re.IGNORECASE)
                for sentence in sentences:
                    m = pattern.search(sentence)
                    if m:
                        best_match = m.group(0)
                        evidence_snippet = sentence[:300]
                        break
                if best_match:
                    break

            if best_match:
                # Infer proficiency and confidence based on evidence cues
                proficiency = self._infer_proficiency(evidence_snippet)
                years_exp = self._extract_years_experience(evidence_snippet)

                confidence = 0.95 if len(evidence_snippet) > 20 else 0.85

                extracted.append(
                    ExtractedSkill(
                        skill_name=info["name"],
                        normalized_name=norm_key,
                        category=info["category"],
                        confidence=confidence,
                        years_experience=years_exp,
                        proficiency_level=proficiency,
                        evidence_text=evidence_snippet,
                    )
                )

        log.info("skills_extracted", total_detected=len(extracted))
        return extracted

    def _infer_proficiency(self, evidence: str) -> str:
        """Determines proficiency level based on surrounding context in evidence."""
        ev_lower = evidence.lower()
        if any(w in ev_lower for w in ["lead", "architect", "expert", "spearheaded", "principal", "founded", "5+ years", "10+ years"]):
            return "expert"
        if any(w in ev_lower for w in ["senior", "designed", "optimized", "scaled", "production", "built", "managed", "3+ years"]):
            return "advanced"
        if any(w in ev_lower for w in ["developed", "implemented", "created", "worked on", "assisted", "used", "proficient"]):
            return "intermediate"
        return "intermediate"

    def _extract_years_experience(self, evidence: str) -> float | None:
        """Attempts to parse explicit years mentioned in the sentence."""
        match = re.search(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\b", evidence, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
