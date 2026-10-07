from __future__ import annotations

import io

from pypdf import PdfReader

from app.core.exceptions import UnsupportedFileTypeException


class PdfParser:
    """Extracts plain text from PDF, DOCX, or TXT files."""

    def extract_text(self, content: bytes, ext: str) -> str:
        if ext == "pdf":
            return self._extract_pdf(content)
        elif ext == "txt":
            return content.decode("utf-8", errors="replace")
        elif ext == "docx":
            return self._extract_docx(content)
        else:
            raise UnsupportedFileTypeException(f"Unsupported extension: {ext}")

    def _extract_pdf(self, content: bytes) -> str:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    def _extract_docx(self, content: bytes) -> str:
        try:
            import docx  # python-docx optional
            doc = docx.Document(io.BytesIO(content))
            return "\n".join(para.text for para in doc.paragraphs if para.text.strip())
        except ImportError:
            raise UnsupportedFileTypeException(
                "python-docx not installed; upload PDF or TXT instead"
            )
