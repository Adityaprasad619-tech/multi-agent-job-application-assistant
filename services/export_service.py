"""
PDF Export Service
===================
Generates clean, professionally formatted PDF files in-memory using ReportLab.
Allows direct downlods in Streamlit via st.download_button().
"""

from __future__ import annotations

import io
from loguru import logger

# Import ReportLab layout elements
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


class ExportService:
    """Service to generate elegant PDF documents for job application resources."""

    @staticmethod
    def _create_base_pdf(title: str, elements: list) -> bytes:
        """Helper to compile a ReportLab doc template into PDF bytes."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        try:
            doc.build(elements)
            pdf_data = buffer.getvalue()
            buffer.close()
            return pdf_data
        except Exception as e:
            logger.error("Failed to generate PDF document: {}", e)
            raise RuntimeError(f"PDF creation failed: {e}") from e

    @classmethod
    def generate_cover_letter_pdf(
        self,
        job_title: str,
        organization: str,
        content: str,
    ) -> bytes:
        """
        Generate a professional Cover Letter PDF.

        Parameters
        ----------
        job_title : str
            Title of the target role.
        organization : str
            Target company/agency.
        content : str
            Full cover letter text.

        Returns
        -------
        bytes
            In-memory PDF bytes.
        """
        styles = getSampleStyleSheet()
        
        # Define clean, professional styling using sans-serif (Helvetica)
        title_style = ParagraphStyle(
            name="CLTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor="#0f172a",  # Sleek dark slate
            spaceAfter=15,
        )
        
        meta_style = ParagraphStyle(
            name="CLMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor="#475569",  # Gray
            spaceAfter=25,
        )
        
        body_style = ParagraphStyle(
            name="CLBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            textColor="#1e293b",
            spaceAfter=12,
        )

        elements = []
        # Header
        elements.append(Paragraph("COVER LETTER", title_style))
        elements.append(Paragraph(f"Position: {job_title} | Organization: {organization}", meta_style))
        elements.append(Spacer(1, 10))

        # Cover letter body paragraphs
        paragraphs = content.split("\n\n")
        for para in paragraphs:
            para_clean = para.strip().replace("\n", "<br/>")
            if para_clean:
                elements.append(Paragraph(para_clean, body_style))

        return self._create_base_pdf("Cover Letter", elements)

    @classmethod
    def generate_recommendations_pdf(
        self,
        job_title: str,
        organization: str,
        recommendations: list[str],
        professional_summary: str = "",
    ) -> bytes:
        """
        Generate a Resume Tailoring Guide PDF.

        Parameters
        ----------
        job_title : str
            Title of the target role.
        organization : str
            Target company/agency.
        recommendations : list[str]
            Actionable tailoring bullet points.
        professional_summary : str
            Tailored professional summary (optional).

        Returns
        -------
        bytes
            In-memory PDF bytes.
        """
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="RecTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor="#1e3a8a",  # Deep navy
            spaceAfter=10,
        )
        
        meta_style = ParagraphStyle(
            name="RecMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor="#4b5563",
            spaceAfter=20,
        )
        
        section_style = ParagraphStyle(
            name="RecSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor="#1e293b",
            spaceBefore=15,
            spaceAfter=10,
        )
        
        body_style = ParagraphStyle(
            name="RecBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11,
            leading=15,
            textColor="#1f2937",
            spaceAfter=10,
        )
        
        bullet_style = ParagraphStyle(
            name="RecBullet",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor="#374151",
            leftIndent=20,
            firstLineIndent=-10,
            spaceAfter=8,
        )

        elements = []
        elements.append(Paragraph("RESUME TAILORING GUIDE", title_style))
        elements.append(Paragraph(f"Role Alignment for: {job_title} at {organization}", meta_style))
        elements.append(Spacer(1, 10))

        if professional_summary:
            elements.append(Paragraph("Tailored Professional Summary Summary", section_style))
            elements.append(Paragraph(professional_summary, body_style))
            elements.append(Spacer(1, 10))

        elements.append(Paragraph("Actionable Recommendations", section_style))
        for i, rec in enumerate(recommendations, 1):
            bullet_text = f"<b>{i}.</b> {rec}"
            elements.append(Paragraph(bullet_text, bullet_style))

        return self._create_base_pdf("Resume Tailoring Guide", elements)

    @classmethod
    def generate_outreach_pdf(
        self,
        job_title: str,
        organization: str,
        linkedin_msg: str,
        recruiter_email: str,
        followup_msg: str,
    ) -> bytes:
        """
        Generate a Networking Outreach Pack PDF containing all messaging templates.

        Parameters
        ----------
        job_title : str
            Title of the target role.
        organization : str
            Target company/agency.
        linkedin_msg : str
            LinkedIn connection note.
        recruiter_email : str
            Cold recruiter email draft.
        followup_msg : str
            Follow-up email sequence draft.

        Returns
        -------
        bytes
            In-memory PDF bytes.
        """
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            name="OutTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=20,
            leading=24,
            textColor="#0f766e",  # Rich teal
            spaceAfter=10,
        )
        
        meta_style = ParagraphStyle(
            name="OutMeta",
            parent=styles["Normal"],
            fontName="Helvetica-Oblique",
            fontSize=10,
            leading=14,
            textColor="#4b5563",
            spaceAfter=20,
        )
        
        section_style = ParagraphStyle(
            name="OutSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor="#1e293b",
            spaceBefore=15,
            spaceAfter=8,
        )
        
        body_style = ParagraphStyle(
            name="OutBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor="#1f2937",
            spaceAfter=15,
        )

        elements = []
        elements.append(Paragraph("NETWORKING OUTREACH KIT", title_style))
        elements.append(Paragraph(f"Outreach Resources for {job_title} at {organization}", meta_style))
        elements.append(Spacer(1, 10))

        # Section 1: LinkedIn Note
        elements.append(Paragraph("1. LinkedIn Connection Request (under 300 chars)", section_style))
        elements.append(Paragraph(f"<i>\"{linkedin_msg}\"</i>", body_style))
        elements.append(Spacer(1, 10))

        # Section 2: Cold Email
        elements.append(Paragraph("2. Recruiter Outreach Email", section_style))
        email_clean = recruiter_email.replace("\n", "<br/>")
        elements.append(Paragraph(email_clean, body_style))
        elements.append(Spacer(1, 10))

        # Section 3: Follow Up
        elements.append(Paragraph("3. Polite Follow-Up Message", section_style))
        followup_clean = followup_msg.replace("\n", "<br/>")
        elements.append(Paragraph(followup_clean, body_style))

        return self._create_base_pdf("Networking Outreach Pack", elements)
