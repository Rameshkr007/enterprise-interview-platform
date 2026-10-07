from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

import structlog

log = structlog.get_logger(__name__)


@dataclass
class ParsedSection:
    section_type: str
    heading: str
    content: str
    sequence_order: int


@dataclass
class ResumeParseResult:
    clean_text: str
    contact_info: dict[str, str]
    sections: list[ParsedSection]
    word_count: int


class ResumeParserService:
    """Advanced multi-pass resume text cleaner, sectionizer, and metadata extractor."""

    # Canonical section classification mappings
    SECTION_PATTERNS: dict[str, list[re.Pattern]] = {
        "summary": [
            re.compile(r"^(?:professional\s+)?summary\b", re.IGNORECASE),
            re.compile(r"^about(?:\s+me)?\b", re.IGNORECASE),
            re.compile(r"^(?:career\s+)?objective\b", re.IGNORECASE),
            re.compile(r"^executive\s+summary\b", re.IGNORECASE),
            re.compile(r"^profile\b", re.IGNORECASE),
        ],
        "experience": [
            re.compile(r"^(?:work\s+|professional\s+|employment\s+)?experience\b", re.IGNORECASE),
            re.compile(r"^work\s+history\b", re.IGNORECASE),
            re.compile(r"^career\s+history\b", re.IGNORECASE),
            re.compile(r"^employment\s+history\b", re.IGNORECASE),
        ],
        "education": [
            re.compile(r"^education(?:al\s+background)?\b", re.IGNORECASE),
            re.compile(r"^academic(?:\s+background|\s+qualifications)?\b", re.IGNORECASE),
            re.compile(r"^degrees(?:\s+and\s+certifications)?\b", re.IGNORECASE),
        ],
        "skills": [
            re.compile(r"^(?:technical\s+|core\s+|key\s+)?skills\b", re.IGNORECASE),
            re.compile(r"^technologies(?:\s+and\s+tools)?\b", re.IGNORECASE),
            re.compile(r"^tech(?:\s+)?stack\b", re.IGNORECASE),
            re.compile(r"^competencies\b", re.IGNORECASE),
            re.compile(r"^proficiencies\b", re.IGNORECASE),
        ],
        "projects": [
            re.compile(r"^(?:technical\s+|key\s+|selected\s+|personal\s+)?projects\b", re.IGNORECASE),
            re.compile(r"^portfolio\b", re.IGNORECASE),
            re.compile(r"^open\s+source\b", re.IGNORECASE),
        ],
        "certifications": [
            re.compile(r"^(?:licenses\s+and\s+)?certifications?\b", re.IGNORECASE),
            re.compile(r"^certificates?\b", re.IGNORECASE),
            re.compile(r"^credentials?\b", re.IGNORECASE),
        ],
        "awards": [
            re.compile(r"^(?:honors\s+and\s+)?awards\b", re.IGNORECASE),
            re.compile(r"^achievements\b", re.IGNORECASE),
        ],
    }

    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    PHONE_PATTERN = re.compile(r"(?:(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})")
    LINKEDIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+", re.IGNORECASE)
    GITHUB_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[A-Za-z0-9_-]+", re.IGNORECASE)

    def parse_resume_text(self, raw_text: str) -> ResumeParseResult:
        """Executes text normalization, contact extraction, and section segmenting."""
        cleaned = self._clean_text(raw_text)
        contact_info = self._extract_contact_info(cleaned)
        sections = self._segment_sections(cleaned)

        word_count = len(cleaned.split())
        log.info(
            "resume_text_parsed",
            word_count=word_count,
            section_count=len(sections),
            detected_sections=[s.section_type for s in sections],
        )

        return ResumeParseResult(
            clean_text=cleaned,
            contact_info=contact_info,
            sections=sections,
            word_count=word_count,
        )

    def _clean_text(self, text: str) -> str:
        """Standardizes line breaks, whitespace, bullet points, and ligatures."""
        if not text:
            return ""

        # Normalize unicode ligatures
        text = text.replace("\uf0b7", "-").replace("\u2022", "-").replace("\u25cf", "-")
        text = text.replace("\u2013", "-").replace("\u2014", "-").replace("\u2019", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')

        # Standardize carriage returns
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Collapse excessive blank lines (> 2) to 2
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove null bytes and trailing spaces
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    def _extract_contact_info(self, text: str) -> dict[str, str]:
        """Extracts candidate contact details using regex heuristics."""
        info: dict[str, str] = {}

        # Look in the first 1000 characters for contact info
        header_text = text[:1200]

        email_match = self.EMAIL_PATTERN.search(header_text)
        if email_match:
            info["email"] = email_match.group(0).lower()

        phone_match = self.PHONE_PATTERN.search(header_text)
        if phone_match:
            info["phone"] = phone_match.group(0).strip()

        linkedin_match = self.LINKEDIN_PATTERN.search(header_text)
        if linkedin_match:
            info["linkedin"] = linkedin_match.group(0)

        github_match = self.GITHUB_PATTERN.search(header_text)
        if github_match:
            info["github"] = github_match.group(0)

        # Candidate name heuristic: first non-empty line before email if short
        lines = [l for l in header_text.split("\n") if l.strip()]
        if lines:
            first_line = lines[0].strip()
            # If the first line doesn't look like an email or phone, consider it a potential name
            if not self.EMAIL_PATTERN.search(first_line) and len(first_line.split()) <= 4 and len(first_line) < 50:
                info["candidate_name"] = first_line

        return info

    def _classify_heading(self, line: str) -> str | None:
        """Returns the section type if the line looks like a known section header."""
        cleaned_line = line.strip(" :-=#*\t").strip()
        if not cleaned_line or len(cleaned_line) > 50 or len(cleaned_line.split()) > 5:
            return None

        for section_type, patterns in self.SECTION_PATTERNS.items():
            for pat in patterns:
                if pat.search(cleaned_line):
                    return section_type
        return None

    def _segment_sections(self, text: str) -> list[ParsedSection]:
        """Splits document text into logical sections based on detected headings."""
        lines = text.split("\n")
        sections: list[ParsedSection] = []

        current_heading = "Header & Contact Info"
        current_type = "contact"
        current_lines: list[str] = []
        seq = 0

        for line in lines:
            line_str = line.strip()
            if not line_str:
                current_lines.append("")
                continue

            detected_type = self._classify_heading(line_str)
            # Only trigger section split if the line is isolated or looks like a heading
            if detected_type is not None:
                # Flush previous section if it has content
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append(
                        ParsedSection(
                            section_type=current_type,
                            heading=current_heading,
                            content=content,
                            sequence_order=seq,
                        )
                    )
                    seq += 1

                current_heading = line_str
                current_type = detected_type
                current_lines = []
            else:
                current_lines.append(line_str)

        # Flush the final section
        content = "\n".join(current_lines).strip()
        if content:
            sections.append(
                ParsedSection(
                    section_type=current_type,
                    heading=current_heading,
                    content=content,
                    sequence_order=seq,
                )
            )

        # If no sections were identified (e.g. unconventional formatting), treat whole text as general body
        if not sections and text.strip():
            sections.append(
                ParsedSection(
                    section_type="general",
                    heading="Resume Body",
                    content=text.strip(),
                    sequence_order=0,
                )
            )

        return sections
