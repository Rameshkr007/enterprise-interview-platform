from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

from app.services.skill_extractor import SkillExtractor

log = structlog.get_logger(__name__)


@dataclass
class ParsedRequirement:
    requirement_text: str
    category: str
    is_required: bool
    importance: float
    skills: list[str]


@dataclass
class JobParseResult:
    title: str
    company: str | None
    seniority_level: str
    min_years_experience: float
    education_required: str
    location_type: str
    requirements: list[ParsedRequirement]
    all_skills: list[str]
    sections: dict[str, str]


class JobRequirementParser:
    """Parses raw Job Descriptions into structured requirements, seniority metrics, and skill needs."""

    SECTION_PATTERNS = {
        "required": [
            re.compile(r"^(?:minimum\s+|basic\s+|required\s+)?qualifications\b", re.IGNORECASE),
            re.compile(r"^what\s+(?:you\s+need|you\'ll\s+need|we\'re\s+looking\s+for)\b", re.IGNORECASE),
            re.compile(r"^requirements\b", re.IGNORECASE),
            re.compile(r"^must[\s-]haves?\b", re.IGNORECASE),
        ],
        "preferred": [
            re.compile(r"^(?:preferred|bonus|nice[\s-]to[\s-]have)\s+(?:qualifications|skills)?\b", re.IGNORECASE),
            re.compile(r"^what\s+(?:would\s+be\s+nice|is\s+a\s+plus)\b", re.IGNORECASE),
        ],
        "responsibilities": [
            re.compile(r"^(?:key\s+|core\s+)?responsibilities\b", re.IGNORECASE),
            re.compile(r"^what\s+you\'ll\s+do\b", re.IGNORECASE),
            re.compile(r"^duties\b", re.IGNORECASE),
        ],
        "about": [
            re.compile(r"^about\s+(?:us|the\s+role|the\s+team|the\s+company)\b", re.IGNORECASE),
            re.compile(r"^overview\b", re.IGNORECASE),
        ],
    }

    def __init__(self) -> None:
        self.skill_extractor = SkillExtractor()

    def parse_job_description(self, raw_text: str, title: str = "", company: str | None = None) -> JobParseResult:
        """Deconstructs JD text into categorized requirements, experience expectations, and skill demands."""
        cleaned = self._clean_text(raw_text)
        sections = self._segment_sections(cleaned)

        seniority = self._infer_seniority(title, cleaned)
        min_years = self._extract_min_experience(cleaned)
        education = self._infer_education(cleaned)
        location = self._infer_location(cleaned)

        requirements: list[ParsedRequirement] = []
        all_skills_set: set[str] = set()

        for sec_name, sec_text in sections.items():
            is_req_section = sec_name in ("required", "responsibilities")
            lines = [l.strip() for l in sec_text.split("\n") if l.strip()]

            for line in lines:
                if len(line) < 15:
                    continue

                # Detect if clause itself has override indicators
                is_preferred = bool(re.search(r"\b(?:preferred|plus|bonus|nice\s+to\s+have)\b", line, re.IGNORECASE))
                is_req = is_req_section and not is_preferred

                # Extract skills referenced in this line
                detected_skills = self.skill_extractor.extract_skills(line)
                skill_names = [s.skill_name for s in detected_skills]
                for s in skill_names:
                    all_skills_set.add(s)

                importance = 1.5 if is_req else 1.0

                requirements.append(
                    ParsedRequirement(
                        requirement_text=line,
                        category=sec_name,
                        is_required=is_req,
                        importance=importance,
                        skills=skill_names,
                    )
                )

        # If no explicit sections were parsed, break whole text by sentences
        if not requirements:
            sentences = re.split(r"(?<=[.!?\n])\s+", cleaned)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 20:
                    detected_skills = self.skill_extractor.extract_skills(sent)
                    skill_names = [s.skill_name for s in detected_skills]
                    for s in skill_names:
                        all_skills_set.add(s)
                    requirements.append(
                        ParsedRequirement(
                            requirement_text=sent,
                            category="general",
                            is_required=True,
                            importance=1.0,
                            skills=skill_names,
                        )
                    )

        log.info(
            "job_description_parsed",
            title=title,
            seniority=seniority,
            min_years=min_years,
            requirements_count=len(requirements),
            skills_count=len(all_skills_set),
        )

        return JobParseResult(
            title=title or "Software Engineer",
            company=company,
            seniority_level=seniority,
            min_years_experience=min_years,
            education_required=education,
            location_type=location,
            requirements=requirements,
            all_skills=sorted(list(all_skills_set)),
            sections=sections,
        )

    def _clean_text(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = text.replace("\uf0b7", "-").replace("\u2022", "-")
        return re.sub(r"\n{3,}", "\n\n", text).strip()

    def _segment_sections(self, text: str) -> dict[str, str]:
        lines = text.split("\n")
        sections: dict[str, list[str]] = {}
        current_sec = "about"
        sections[current_sec] = []

        for line in lines:
            line_str = line.strip(" :-=*#\t").strip()
            if not line_str:
                continue

            detected = None
            if len(line_str) < 60 and len(line_str.split()) <= 6:
                for sec_type, pats in self.SECTION_PATTERNS.items():
                    for pat in pats:
                        if pat.search(line_str):
                            detected = sec_type
                            break
                    if detected:
                        break

            if detected:
                current_sec = detected
                if current_sec not in sections:
                    sections[current_sec] = []
            else:
                sections[current_sec].append(line.strip())

        return {k: "\n".join(v).strip() for k, v in sections.items() if v}

    def _infer_seniority(self, title: str, text: str) -> str:
        t_title = title.lower()
        if any(w in t_title for w in ["principal", "distinguished", "fellow"]):
            return "principal"
        if any(w in t_title for w in ["staff", "lead", "architect"]):
            return "staff"
        if any(w in t_title for w in ["senior", "sr.", "sr "]):
            return "senior"
        if any(w in t_title for w in ["junior", "jr.", "entry", "intern", "associate"]):
            return "entry"

        t_lower = text[:500].lower()
        if any(w in t_lower for w in ["principal", "distinguished"]):
            return "principal"
        if any(w in t_lower for w in ["staff engineer", "lead engineer"]):
            return "staff"
        if any(w in t_lower for w in ["senior engineer", "senior developer", "sr."]):
            return "senior"
        return "mid"

    def _extract_min_experience(self, text: str) -> float:
        matches = re.findall(r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+relevant|\s+professional|\s+experience|\s+working)", text, re.IGNORECASE)
        if matches:
            try:
                nums = [float(m) for m in matches]
                return min(nums)  # The minimum threshold stated
            except ValueError:
                pass
        return 2.0  # default reasonable baseline

    def _infer_education(self, text: str) -> str:
        t_lower = text.lower()
        if "ph.d" in t_lower or "phd" in t_lower:
            return "Ph.D."
        if "master" in t_lower or "m.s." in t_lower or "ms in" in t_lower:
            return "Master's Degree"
        if "bachelor" in t_lower or "b.s." in t_lower or "bs in" in t_lower or "degree in computer science" in t_lower:
            return "Bachelor's Degree"
        return "Bachelor's or equivalent experience"

    def _infer_location(self, text: str) -> str:
        t_lower = text.lower()
        if "remote" in t_lower:
            return "remote"
        if "hybrid" in t_lower:
            return "hybrid"
        if "on-site" in t_lower or "onsite" in t_lower:
            return "onsite"
        return "remote"
