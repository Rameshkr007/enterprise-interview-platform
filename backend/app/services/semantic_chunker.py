from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.services.resume_parser_service import ParsedSection


@dataclass
class SemanticChunk:
    chunk_index: int
    chunk_text: str
    token_count: int
    section_type: str
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticChunker:
    """Sliding-window semantic chunker respecting natural paragraph and sentence boundaries."""

    def __init__(
        self,
        target_token_limit: int = 350,
        token_overlap: int = 50,
    ) -> None:
        self.target_token_limit = target_token_limit
        self.token_overlap = token_overlap
        self.sentence_regex = re.compile(r"(?<=[.!?])\s+")

    def chunk_sections(self, sections: list[ParsedSection]) -> list[SemanticChunk]:
        """Iterates through document sections and produces context-aware semantic chunks."""
        all_chunks: list[SemanticChunk] = []
        global_index = 0

        for section in sections:
            section_chunks = self._chunk_single_section(section, start_index=global_index)
            all_chunks.extend(section_chunks)
            global_index += len(section_chunks)

        return all_chunks

    def _estimate_tokens(self, text: str) -> int:
        """Approximates token count based on whitespace word count multiplied by standard subword ratio."""
        words = len(text.split())
        return int(words * 1.3)

    def _chunk_single_section(self, section: ParsedSection, start_index: int) -> list[SemanticChunk]:
        """Splits a single section into overlapping chunks if it exceeds the target size."""
        text = section.content.strip()
        if not text:
            return []

        section_prefix = f"[{section.heading.upper()}] "
        prefix_tokens = self._estimate_tokens(section_prefix)
        usable_budget = max(self.target_token_limit - prefix_tokens, 100)

        # Break text into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        chunks: list[SemanticChunk] = []
        current_sentences: list[str] = []
        current_tokens = 0
        chunk_idx = start_index

        for para in paragraphs:
            # Further break paragraph into sentences
            sentences = self.sentence_regex.split(para)
            for sentence in sentences:
                sent_clean = sentence.strip()
                if not sent_clean:
                    continue

                sent_tokens = self._estimate_tokens(sent_clean)

                # If adding this sentence exceeds budget and we already have content, finalize current chunk
                if current_tokens + sent_tokens > usable_budget and current_sentences:
                    chunk_body = " ".join(current_sentences)
                    full_chunk_text = f"{section_prefix}{chunk_body}".strip()
                    chunks.append(
                        SemanticChunk(
                            chunk_index=chunk_idx,
                            chunk_text=full_chunk_text,
                            token_count=self._estimate_tokens(full_chunk_text),
                            section_type=section.section_type,
                            metadata={
                                "section_heading": section.heading,
                                "section_type": section.section_type,
                                "sequence_order": section.sequence_order,
                            },
                        )
                    )
                    chunk_idx += 1

                    # Retain overlap sentences
                    overlap_sentences: list[str] = []
                    overlap_count = 0
                    for s in reversed(current_sentences):
                        s_tokens = self._estimate_tokens(s)
                        if overlap_count + s_tokens <= self.token_overlap:
                            overlap_sentences.insert(0, s)
                            overlap_count += s_tokens
                        else:
                            break

                    current_sentences = overlap_sentences
                    current_tokens = overlap_count

                current_sentences.append(sent_clean)
                current_tokens += sent_tokens

        # Flush final remaining sentences
        if current_sentences:
            chunk_body = " ".join(current_sentences)
            full_chunk_text = f"{section_prefix}{chunk_body}".strip()
            chunks.append(
                SemanticChunk(
                    chunk_index=chunk_idx,
                    chunk_text=full_chunk_text,
                    token_count=self._estimate_tokens(full_chunk_text),
                    section_type=section.section_type,
                    metadata={
                        "section_heading": section.heading,
                        "section_type": section.section_type,
                        "sequence_order": section.sequence_order,
                    },
                )
            )

        return chunks
