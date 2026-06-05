"""
Resume Profile Extraction Tests
===============================
Validates that raw resume text is parsed correctly into the StructuredResumeProfile
schema, and that all nested objects (ExperienceItem, ProjectItem) parse successfully.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from schemas.resume_profile import StructuredResumeProfile, ExperienceItem, ProjectItem
from schemas.mock_data import generate_mock_resume_profile
from crews.resume_profile_crew import ResumeProfileCrew
from utils.config import AppConfig


def test_structured_resume_profile_schemas():
    """Verify that Pydantic validation handles nested schemas correctly."""
    # Given
    profile = StructuredResumeProfile(
        technical_skills=["Python", "PostgreSQL"],
        experience=[
            ExperienceItem(
                title="Lead Developer",
                company="Acme Corp",
                summary="Built backend systems in Python.",
            )
        ],
        projects=[
            ProjectItem(
                name="SaaS App",
                technologies=["Django", "React"],
                summary="Developed a multi-tenant cloud application.",
            )
        ],
        education=["B.S. in Computer Science"],
        achievements=["Employee of the Year"],
        certifications=["AWS Solutions Architect"],
    )

    # Then
    assert isinstance(profile, StructuredResumeProfile)
    assert len(profile.technical_skills) == 2
    assert len(profile.experience) == 1
    assert profile.experience[0].title == "Lead Developer"
    assert profile.experience[0].company == "Acme Corp"
    assert profile.experience[0].summary == "Built backend systems in Python."
    assert len(profile.projects) == 1
    assert profile.projects[0].name == "SaaS App"
    assert profile.projects[0].technologies == ["Django", "React"]
    assert profile.projects[0].summary == "Developed a multi-tenant cloud application."
    assert profile.education == ["B.S. in Computer Science"]
    assert profile.achievements == ["Employee of the Year"]
    assert profile.certifications == ["AWS Solutions Architect"]


def test_resume_profile_crew_mock_resolution():
    """Verify that ResumeProfileCrew correctly runs and extracts profile in test mode."""
    # Given
    env_patch = {
        "GROQ_API_KEY": "test-key",
        "USAJOBS_API_KEY": "test-key",
        "USAJOBS_EMAIL": "test@test.com",
        "TEST_MODE": "true",
    }
    with patch.dict(os.environ, env_patch):
        from utils.config import load_config
        config = load_config()
        assert config.test_mode is True

        # When
        crew = ResumeProfileCrew(config)
        profile = crew.run("Mock raw resume text that needs parsing")

    # Then
    assert isinstance(profile, StructuredResumeProfile)
    assert "Python" in profile.technical_skills
    assert len(profile.experience) > 0
    assert isinstance(profile.experience[0], ExperienceItem)
    assert profile.experience[0].company == "OKC Tech Solutions"
    assert len(profile.projects) > 0
    assert isinstance(profile.projects[0], ProjectItem)
    assert "Aviation Safety Monitor" in profile.projects[0].name
