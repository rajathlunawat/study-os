"""
StudyOS Document Service — Parser.

Responsibility: Extracts raw text from uploaded files (PDF, TXT, MD).
Isolates the PyMuPDF (fitz) dependency.
Contains no database logic or chunking logic.
"""

from pathlib import Path
import fitz  # PyMuPDF

from app.core.exceptions import DocumentParsingError


class DocumentParser:
    """
    Handles the extraction of text from various file formats.
    Currently supports PDF, TXT, and MD.
    """

    @staticmethod
    def extract_text(file_path: Path) -> str:
        """
        Extract text from a file based on its extension.

        Args:
            file_path: Absolute or relative path to the file on disk.

        Returns:
            The raw, uncleaned text extracted from the entire document.

        Raises:
            DocumentParsingError: If the file type is unsupported or extraction fails.
        """
        if not file_path.exists():
            raise DocumentParsingError(f"File not found: {file_path}")

        suffix = file_path.suffix.lower()

        try:
            if suffix == ".pdf":
                return DocumentParser._parse_pdf(file_path)
            elif suffix in {".txt", ".md"}:
                return DocumentParser._parse_text_file(file_path)
            else:
                raise DocumentParsingError(f"Unsupported file extension: {suffix}")
                
        except Exception as e:
            # Catching generic Exception because PyMuPDF can raise various C-level errors
            raise DocumentParsingError(
                message=f"Failed to parse document '{file_path.name}'.",
                details={"error": str(e)}
            ) from e

    @staticmethod
    def _parse_pdf(file_path: Path) -> str:
        """
        Extract text from a PDF using PyMuPDF.
        """
        text_pages = []
        
        # Using context manager to ensure the PDF document is closed properly
        with fitz.open(str(file_path)) as pdf_doc:
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                # extract_text() gets plain text. 
                # (For advanced extraction, fitz supports blocks/dicts, but plain text is best for RAG)
                page_text = page.get_text()
                if page_text:
                    text_pages.append(page_text)
                    
        return "\n\n".join(text_pages)

    @staticmethod
    def _parse_text_file(file_path: Path) -> str:
        """
        Extract text from standard plain text or markdown files.
        """
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
