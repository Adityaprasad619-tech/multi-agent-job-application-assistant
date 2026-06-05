"""
Resume Parser Service
=====================
Extracts raw text content from uploaded PDF and DOCX files.
Handles error cases, corrupted files, and file size limits gracefully.
"""

from __future__ import annotations

import io
from pathlib import Path
from loguru import logger

# Import third-party parsing tools
import pypdf
import docx


class ResumeParsingError(Exception):
    """Custom exception raised when resume text extraction fails."""

    pass


class ResumeParserService:
    """Service class for parsing text out of resumes of various formats."""

    @staticmethod
    def parse_pdf(file_bytes: bytes) -> str:
        """
        Extract text from raw PDF bytes.

        Parameters
        ----------
        file_bytes : bytes
            Binary PDF data.

        Returns
        -------
        str
            Extracted clean text.

        Raises
        ------
        ResumeParsingError
            If file is corrupted or text extraction fails.
        """
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file)
            
            if len(reader.pages) == 0:
                raise ResumeParsingError("The uploaded PDF resume contains no pages.")

            extracted_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    extracted_text.append(text)
                else:
                    logger.warning("No text extracted from PDF page {}", i + 1)

            full_text = "\n".join(extracted_text).strip()
            if not full_text:
                raise ResumeParsingError(
                    "No readable text could be extracted from the PDF. It may contain scanned images only."
                )

            logger.info("Successfully extracted {} characters from PDF", len(full_text))
            return full_text

        except Exception as e:
            if isinstance(e, ResumeParsingError):
                raise
            logger.error("PDF Parsing failed: {}", e)
            raise ResumeParsingError(f"Failed to parse PDF resume: {e}") from e

    @staticmethod
    def parse_docx(file_bytes: bytes) -> str:
        """
        Extract text from raw Word DOCX bytes.

        Parameters
        ----------
        file_bytes : bytes
            Binary DOCX data.

        Returns
        -------
        str
            Extracted clean text.

        Raises
        ------
        ResumeParsingError
            If file is corrupted or text extraction fails.
        """
        try:
            docx_file = io.BytesIO(file_bytes)
            doc = docx.Document(docx_file)
            
            paragraphs_text = [p.text for p in doc.paragraphs if p.text.strip()]
            
            # Also extract text from tables if any exist
            tables_text = []
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            tables_text.append(cell.text.strip())

            all_text = paragraphs_text + tables_text
            full_text = "\n".join(all_text).strip()
            
            if not full_text:
                raise ResumeParsingError("Word document contains no readable text content.")

            logger.info("Successfully extracted {} characters from DOCX", len(full_text))
            return full_text

        except Exception as e:
            if isinstance(e, ResumeParsingError):
                raise
            logger.error("DOCX Parsing failed: {}", e)
            raise ResumeParsingError(f"Failed to parse DOCX resume: {e}") from e

    @staticmethod
    def normalize_text(text: str) -> str:
        """
        Normalize text extracted from PDF/DOCX resumes.
        Detects character-spaced patterns (e.g., 'P y t h o n') and merges them,
        while preserving standard sentence structure and clearing out excessive spacing.

        Parameters
        ----------
        text : str
            Raw extracted text from resume.

        Returns
        -------
        str
            Cleaned and normalized text.
        """
        import re
        if not text:
            return ""

        lines = text.splitlines()
        normalized_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                normalized_lines.append("")
                continue

            # 1. Split by two or more spaces to preserve word boundaries
            parts = re.split(r"\s{2,}", stripped)
            normalized_parts = []

            for part in parts:
                sub_words = part.split(" ")
                new_words = []
                current_seq = []

                for word in sub_words:
                    if len(word) == 1:
                        current_seq.append(word)
                    else:
                        if current_seq:
                            if len(current_seq) >= 2:
                                new_words.append("".join(current_seq))
                            else:
                                new_words.extend(current_seq)
                            current_seq = []
                        new_words.append(word)

                if current_seq:
                    if len(current_seq) >= 2:
                        new_words.append("".join(current_seq))
                    else:
                        new_words.extend(current_seq)

                normalized_parts.append(" ".join(new_words))

            # 2. Join the parts back and normalize any remaining multiple spaces
            normalized_line = " ".join(normalized_parts)
            normalized_line = re.sub(r"\s+", " ", normalized_line).strip()
            normalized_lines.append(normalized_line)

        return "\n".join(normalized_lines)

    def parse_resume(self, file_name: str, file_content: bytes) -> str:
        """
        Autodetect extension, parse resume text, and normalize character-spaced patterns.

        Parameters
        ----------
        file_name : str
            Name of the file (e.g. 'resume.pdf').
        file_content : bytes
            Raw binary content of the file.

        Returns
        -------
        str
            Extracted, normalized clean text content.

        Raises
        ------
        ValueError
            If file extension is unsupported.
        ResumeParsingError
            If parsing fails.
        """
        suffix = Path(file_name).suffix.lower()
        if suffix == ".pdf":
            raw_text = self.parse_pdf(file_content)
        elif suffix in [".docx", ".doc"]:
            raw_text = self.parse_docx(file_content)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Please upload a PDF or DOCX file.")

        return self.normalize_text(raw_text)



