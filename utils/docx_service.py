from __future__ import annotations

from docx import Document
from docx.document import Document as DocxDocument
from docx.shared import Pt


class DocxService:
    """Reusable DOCX editing helper that preserves the existing document structure."""

    def __init__(self, path: str) -> None:
        self.path = path

    def load(self) -> DocxDocument:
        """Load the target DOCX file."""

        return Document(self.path)

    def replace_text(self, document: DocxDocument, replacements: dict[str, str]) -> None:
        """Replace matching text content in a document while preserving style."""

        for paragraph in document.paragraphs:
            for key, value in replacements.items():
                if key in paragraph.text:
                    paragraph.text = paragraph.text.replace(key, value)

        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    for key, value in replacements.items():
                        if key in cell.text:
                            cell.text = cell.text.replace(key, value)
