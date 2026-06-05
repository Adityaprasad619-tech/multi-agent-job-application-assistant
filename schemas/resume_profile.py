"""
Resume Profile Schema
======================
Pydantic models representing the structured, token-efficient resume profile.
Used to decouple raw resume text parsing from job-specific tailoring.
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class ExperienceItem(BaseModel):
    """Structured experience item representing a single professional role."""

    title: str = Field(
        ...,
        description="The candidate's job title or role designation (e.g., 'Senior Python Developer').",
    )
    company: str = Field(
        ...,
        description="The name of the company, organization, or government agency.",
    )
    summary: str = Field(
        ...,
        description="A concise summary of key responsibilities, contributions, and professional achievements in this role.",
    )


class ProjectItem(BaseModel):
    """Structured project item representing a key project or highlight."""

    name: str = Field(
        ...,
        description="The name of the project.",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="List of primary programming languages, frameworks, databases, or tools used.",
    )
    summary: str = Field(
        ...,
        description="A concise summary of the project goals, implementation details, and outcomes.",
    )


class StructuredResumeProfile(BaseModel):
    """Structured, token-efficient profile extracted from a raw resume."""

    full_name: str | None = Field(
        default=None,
        description="The candidate's full name (e.g., 'John Doe').",
    )
    email: str | None = Field(
        default=None,
        description="The candidate's email address.",
    )
    phone: str | None = Field(
        default=None,
        description="The candidate's phone number.",
    )
    linkedin_url: str | None = Field(
        default=None,
        description="The URL of the candidate's LinkedIn profile.",
    )
    github_url: str | None = Field(
        default=None,
        description="The URL of the candidate's GitHub profile.",
    )
    location: str | None = Field(
        default=None,
        description="The candidate's city, state, or general location.",
    )
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Core technical skills, tools, programming languages, and specialized methodologies.",
    )
    experience: list[ExperienceItem] = Field(
        default_factory=list,
        description="List of structured professional experience items.",
    )
    projects: list[ProjectItem] = Field(
        default_factory=list,
        description="List of structured project items.",
    )
    education: list[str] = Field(
        default_factory=list,
        description="Academic degrees, schools, majors, graduation dates, or relevant coursework.",
    )
    achievements: list[str] = Field(
        default_factory=list,
        description="Key professional accomplishments, awards, publications, or key metrics.",
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="List of professional certifications, licenses, and credentials, if present.",
    )
