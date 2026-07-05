from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from docx import Document


class PdfService:
    """Convert DOCX files to PDF using OS-appropriate tools."""

    def __init__(self) -> None:
        self.system = platform.system().lower()

    def convert(self, docx_path: str | Path, pdf_path: str | Path) -> Path:
        """Convert a DOCX file to PDF if the system tool is available."""

        docx_path = Path(docx_path)
        pdf_path = Path(pdf_path)
        if self.system == "windows":
            command = ["docx2pdf", str(docx_path), str(pdf_path)]
        else:
            command = ["libreoffice", "--headless", "--convert-to", "pdf", str(docx_path), "--outdir", str(pdf_path.parent)]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
        except FileNotFoundError:
            self._write_simple_pdf(docx_path, pdf_path)
            return pdf_path

        if result.returncode == 0 and self.system != "windows":
            expected = pdf_path.parent / f"{docx_path.stem}.pdf"
            if expected.exists():
                expected.replace(pdf_path)
            return pdf_path

        self._write_simple_pdf(docx_path, pdf_path)
        return pdf_path

    def _write_simple_pdf(self, docx_path: Path, pdf_path: Path) -> None:
        """Write a minimal PDF document from the DOCX text as a local fallback."""

        document = Document(docx_path)
        text_lines = [paragraph.text.strip() for paragraph in document.paragraphs if paragraph.text.strip()]
        content_lines = [line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") for line in text_lines]
        content_stream = ""
        y_position = 760
        for line in content_lines or ["Resume generated locally"]:
            content_stream += f"BT /F1 12 Tf 72 {y_position} Td ({line}) Tj ET\n"
            y_position -= 14

        stream_bytes = content_stream.encode("latin-1", "replace")
        objects = [
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
            f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("ascii") + stream_bytes + b"\nendstream\nendobj\n",
            b"5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
        ]

        buffer = bytearray(b"%PDF-1.4\n")
        offsets = []
        for obj in objects:
            offsets.append(len(buffer))
            buffer.extend(obj)
        startxref = len(buffer)
        buffer.extend(b"xref\n0 6\n")
        buffer.extend(b"0000000000 65535 f \n")
        for offset in offsets:
            buffer.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        buffer.extend(f"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{startxref}\n%%EOF\n".encode("ascii"))
        pdf_path.write_bytes(buffer)
