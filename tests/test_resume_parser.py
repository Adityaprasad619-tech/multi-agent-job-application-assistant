"""
Resume Parser Tests
===================
Tests for ResumeParserService using unit mock patterns.
Verifies PDF, DOCX parsing logic and empty/corrupted file exceptions.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import pytest

from services.resume_parser import ResumeParserService, ResumeParsingError


class TestResumeParser(unittest.TestCase):
    """Test suite for ResumeParserService."""

    def setUp(self) -> None:
        self.parser = ResumeParserService()

    @patch("pypdf.PdfReader")
    def test_parse_pdf_success(self, mock_pdf_reader: MagicMock) -> None:
        """Verify successful PDF text extraction."""
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Candidate Name\nPython Developer\nExperience: 3 years"
        
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader_instance

        # Execute
        result = self.parser.parse_pdf(b"fake_pdf_bytes")

        # Assertions
        self.assertIn("Python Developer", result)
        self.assertIn("3 years", result)
        mock_pdf_reader.assert_called_once()

    @patch("pypdf.PdfReader")
    def test_parse_pdf_empty_error(self, mock_pdf_reader: MagicMock) -> None:
        """Verify handling of empty PDF documents."""
        mock_reader_instance = MagicMock()
        mock_reader_instance.pages = []
        mock_pdf_reader.return_value = mock_reader_instance

        with self.assertRaises(ResumeParsingError):
            self.parser.parse_pdf(b"fake_pdf_bytes")

    @patch("docx.Document")
    def test_parse_docx_success(self, mock_docx: MagicMock) -> None:
        """Verify successful DOCX text extraction."""
        mock_p1 = MagicMock()
        mock_p1.text = "Candidate Profile"
        mock_p2 = MagicMock()
        mock_p2.text = "Skills: SQL, React"

        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = [mock_p1, mock_p2]
        mock_doc_instance.tables = []
        mock_docx.return_value = mock_doc_instance

        # Execute
        result = self.parser.parse_docx(b"fake_docx_bytes")

        # Assertions
        self.assertIn("Candidate Profile", result)
        self.assertIn("Skills: SQL, React", result)

    @patch("docx.Document")
    def test_parse_docx_empty_error(self, mock_docx: MagicMock) -> None:
        """Verify handling of empty DOCX files."""
        mock_doc_instance = MagicMock()
        mock_doc_instance.paragraphs = []
        mock_doc_instance.tables = []
        mock_docx.return_value = mock_doc_instance

        with self.assertRaises(ResumeParsingError):
            self.parser.parse_docx(b"fake_docx_bytes")

    def test_unsupported_format(self) -> None:
        """Verify raising error on unsupported extensions."""
        with self.assertRaises(ValueError):
            self.parser.parse_resume("invalid.txt", b"some bytes")

    def test_normalize_character_spaced_words(self) -> None:
        """Verify that character-spaced words are correctly joined."""
        # Single words
        self.assertEqual(ResumeParserService.normalize_text("P y t h o n"), "Python")
        self.assertEqual(ResumeParserService.normalize_text("S U M M A R Y"), "SUMMARY")
        
        # Multiple character-spaced words with multiple spaces
        self.assertEqual(
            ResumeParserService.normalize_text("P y t h o n   D e v e l o p e r"),
            "Python Developer"
        )
        self.assertEqual(
            ResumeParserService.normalize_text("S r .   S o f t w a r e   E n g i n e e r"),
            "Sr. Software Engineer"
        )

    def test_normalize_mixed_character_spacing(self) -> None:
        """Verify that mixed normal and character-spaced text is resolved correctly."""
        self.assertEqual(
            ResumeParserService.normalize_text("Name: J o h n   D o e"),
            "Name: John Doe"
        )
        self.assertEqual(
            ResumeParserService.normalize_text("Email: j o h n @ d o e . c o m"),
            "Email: john@doe.com"
        )

    def test_normalize_preserves_sentences(self) -> None:
        """Verify that normal English sentences are fully preserved without improper merging."""
        sentence = "I am a Python developer with 3 years of experience at NIH."
        self.assertEqual(ResumeParserService.normalize_text(sentence), sentence)
        
        # Verify single letters next to multi-letter words aren't joined
        self.assertEqual(
            ResumeParserService.normalize_text("He is a developer at a company."),
            "He is a developer at a company."
        )

    def test_normalize_excessive_whitespace(self) -> None:
        """Verify that excessive newlines and double spaces are reduced and cleaned."""
        text_with_spaces = "Python      Developer  with    SQL"
        self.assertEqual(
            ResumeParserService.normalize_text(text_with_spaces),
            "Python Developer with SQL"
        )
        
        text_with_newlines = "Line 1\n\n\nLine 2\nLine 3"
        self.assertEqual(
            ResumeParserService.normalize_text(text_with_newlines),
            "Line 1\n\n\nLine 2\nLine 3"
        )

