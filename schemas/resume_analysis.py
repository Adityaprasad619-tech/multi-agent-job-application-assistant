"""
Resume Analysis Schema
======================
Pydantic model representing structured insights extracted from a user's resume.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeAnalysis(BaseModel):
    """Structured information extracted and summarized from an uploaded resume."""

    extracted_skills: list[str] = Field(
        default_factory=list,
        description="List of technical and soft skills parsed from the resume.",
    )
    strengths: list[str] = Field(
        default_factory=list,
        description="List of career strengths and domain expertise highlighted in the resume.",
    )
    weaknesses: list[str] = Field(
        default_factory=list,
        description="Areas where the resume lacks clear evidence of skills or qualifications.",
    )
    years_of_experience: str = Field(
        ...,
        description="Estimate or summary of overall professional experience (e.g. '5+ years').",
    )
    education_summary: str = Field(
        ...,
        description="Parsed academic background summary (degrees, institutions, certifications).",
    )
