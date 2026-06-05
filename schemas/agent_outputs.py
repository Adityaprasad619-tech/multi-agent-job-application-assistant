"""
Agent Output Schemas
=====================
Pydantic models defining the structured output contract for every agent.

Design Decisions:
- Pydantic v2 BaseModel for validation, serialization, and JSON schema generation.
- These models are the single source of truth for agent output shape.
- Used by CrewAI (output_pydantic), Streamlit (display), and SQLite (storage).
- Field descriptions serve as documentation AND as hints to the LLM via JSON schema.
- CompleteApplicationPackage composes all outputs into one object.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from schemas.resume_analysis import ResumeAnalysis
from schemas.ats_score import ATSScore
from schemas.gap_analysis import GapAnalysis


class JobAnalysisOutput(BaseModel):
    """Structured output from the Job Analyzer agent."""

    role_summary: str = Field(
        ...,
        description="A concise 2-3 sentence summary of the job role, responsibilities, and team.",
    )
    required_skills: list[str] = Field(
        ...,
        description=(
            "List of required hard/technical skills as concise 1-3 word labels. "
            "Each entry must be a skill name, technology, tool, or competency — NOT a sentence. "
            "Example: ['Python', 'Statistical Analysis', 'SQL'] — NOT 'Experience with Python'."
        ),
    )
    preferred_skills: list[str] = Field(
        ...,
        description=(
            "List of preferred/nice-to-have skills as concise 1-3 word labels. "
            "Same formatting rules as required_skills."
        ),
    )
    ats_keywords: list[str] = Field(
        ...,
        description=(
            "Important keywords and phrases an ATS (Applicant Tracking System) "
            "would scan for in a resume targeting this job."
        ),
    )
    experience_requirements: str = Field(
        ...,
        description="Summary of years of experience and domain expertise required.",
    )


class ResumeOutput(BaseModel):
    """Structured output from the Resume & Cover Letter Specialist agent."""

    professional_summary: str = Field(
        ...,
        description=(
            "A 3-4 sentence professional summary tailored to this specific job, "
            "ready to place at the top of a resume."
        ),
    )
    resume_recommendations: list[str] = Field(
        ...,
        description=(
            "Actionable bullet-point recommendations for tailoring a resume "
            "to this job (skills to highlight, projects to feature, keywords to include)."
        ),
    )
    cover_letter: str = Field(
        ...,
        description=(
            "A complete, professional cover letter tailored to the specific job posting. "
            "Should be 3-4 paragraphs with proper greeting and closing."
        ),
    )


class OutreachOutput(BaseModel):
    """Structured output from the Networking & Outreach Specialist agent."""

    linkedin_message: str = Field(
        ...,
        description=(
            "A concise LinkedIn connection request message (under 300 characters) "
            "expressing interest in the role or company."
        ),
    )
    recruiter_message: str = Field(
        ...,
        description=(
            "A professional recruiter outreach email expressing interest in the position, "
            "highlighting relevant qualifications, and requesting a conversation."
        ),
    )
    followup_message: str = Field(
        ...,
        description=(
            "A polite follow-up message to send 5-7 days after initial outreach "
            "if no response has been received."
        ),
    )


class CompleteApplicationPackage(BaseModel):
    """Combined output from all four agents and calculators — the final deliverable."""

    analysis: JobAnalysisOutput = Field(
        ...,
        description="Job analysis results from the Job Analyzer agent.",
    )
    resume_package: ResumeOutput = Field(
        ...,
        description="Resume recommendations and cover letter from the Resume Specialist agent.",
    )
    outreach_package: OutreachOutput = Field(
        ...,
        description="Networking messages from the Outreach Specialist agent.",
    )
    resume_analysis: Optional[ResumeAnalysis] = Field(
        None,
        description="Candidate's parsed resume insights.",
    )
    ats_score: Optional[ATSScore] = Field(
        None,
        description="Deterministic ATS match score and keyword analysis.",
    )
    gap_analysis: Optional[GapAnalysis] = Field(
        None,
        description="Skills audit and gap analysis.",
    )
