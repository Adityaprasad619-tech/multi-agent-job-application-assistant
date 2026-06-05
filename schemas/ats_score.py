"""
ATS Score Schema
=================
Pydantic model representing the output of the deterministic ATS matching engine.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PartialMatch(BaseModel):
    """Represents a skill requirement that was partially satisfied via synonym/taxonomy matching."""

    required_skill: str = Field(
        ...,
        description="The skill or category required by the job posting.",
    )
    matched_via: list[str] = Field(
        default_factory=list,
        description="List of resume skills/technologies that satisfy this requirement through synonym or taxonomy mapping.",
    )


class ATSScore(BaseModel):
    """Output details from the deterministic ATS matching and scoring algorithm."""

    ats_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="The matched score calculated by the deterministic ATS keyword matcher.",
    )
    matched_keywords: list[str] = Field(
        default_factory=list,
        description="List of keywords/skills present in both the resume and the job requirements (direct exact matches).",
    )
    partially_matched_keywords: list[PartialMatch] = Field(
        default_factory=list,
        description="List of job requirements matched indirectly via synonym or taxonomy mapping.",
    )
    missing_keywords: list[str] = Field(
        default_factory=list,
        description="List of keywords/skills required by the job but not matched directly or via taxonomy.",
    )
    recommendations: list[str] = Field(
        default_factory=list,
        description="Actionable recommendations to improve the match score.",
    )
