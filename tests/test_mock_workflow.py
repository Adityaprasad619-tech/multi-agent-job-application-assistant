"""
Mock Workflow Integration Tests
=================================
Validates the full crew workflow in test mode (no Groq API calls).

Tests:
- Mock workflow returns CompleteApplicationPackage.
- All sub-models are correct Pydantic types.
- Mock data is job-specific (interpolates title/org).
- No network calls occur.
- Mock data module independently produces valid outputs.

Run with:
    python -m pytest tests/test_mock_workflow.py -v
    OR
    python tests/test_mock_workflow.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.agent_outputs import (
    CompleteApplicationPackage,
    JobAnalysisOutput,
    OutreachOutput,
    ResumeOutput,
)
from schemas.resume_profile import StructuredResumeProfile
from schemas.mock_data import (
    generate_mock_analysis,
    generate_mock_outreach,
    generate_mock_package,
    generate_mock_resume,
    generate_mock_resume_profile,
)
from services.usajobs_service import JobListing


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def sample_job() -> JobListing:
    """A realistic test job listing."""
    return JobListing(
        position_id="TEST-001",
        title="Data Scientist",
        organization="National Institutes of Health",
        department="Health and Human Services",
        location="Bethesda, MD",
        salary_min="95000",
        salary_max="145000",
        pay_interval="Per Year",
        grade_low="GS-13",
        grade_high="GS-14",
        position_url="https://usajobs.gov/test/123",
        open_date="2026-05-01",
        close_date="2026-06-15",
        description="Conduct data analysis and build ML models for biomedical research.",
        qualifications="Python, R, machine learning, statistics. PhD preferred.",
        who_may_apply="US Citizens",
    )


# ============================================================
# Mock Data Module Tests
# ============================================================
class TestMockDataModule:
    """Test the mock data generators directly."""

    def test_mock_analysis_type(self, sample_job: JobListing) -> None:
        result = generate_mock_analysis(sample_job)
        assert isinstance(result, JobAnalysisOutput)

    def test_mock_analysis_is_job_specific(self, sample_job: JobListing) -> None:
        result = generate_mock_analysis(sample_job)
        assert "Data Scientist" in result.role_summary
        assert "National Institutes of Health" in result.role_summary

    def test_mock_analysis_has_required_fields(self, sample_job: JobListing) -> None:
        result = generate_mock_analysis(sample_job)
        assert len(result.required_skills) > 0
        assert len(result.preferred_skills) > 0
        assert len(result.ats_keywords) > 0
        assert len(result.experience_requirements) > 0

    def test_mock_resume_type(self, sample_job: JobListing) -> None:
        result = generate_mock_resume(sample_job)
        assert isinstance(result, ResumeOutput)

    def test_mock_resume_is_job_specific(self, sample_job: JobListing) -> None:
        result = generate_mock_resume(sample_job)
        assert "Data Scientist" in result.professional_summary
        assert "National Institutes of Health" in result.cover_letter

    def test_mock_resume_has_recommendations(self, sample_job: JobListing) -> None:
        result = generate_mock_resume(sample_job)
        assert len(result.resume_recommendations) >= 3

    def test_mock_outreach_type(self, sample_job: JobListing) -> None:
        result = generate_mock_outreach(sample_job)
        assert isinstance(result, OutreachOutput)

    def test_mock_outreach_is_job_specific(self, sample_job: JobListing) -> None:
        result = generate_mock_outreach(sample_job)
        assert "Data Scientist" in result.linkedin_message
        assert "National Institutes of Health" in result.recruiter_message

    def test_mock_package_type(self, sample_job: JobListing) -> None:
        result = generate_mock_package(sample_job)
        assert isinstance(result, CompleteApplicationPackage)

    def test_mock_package_composition(self, sample_job: JobListing) -> None:
        result = generate_mock_package(sample_job)
        assert isinstance(result.analysis, JobAnalysisOutput)
        assert isinstance(result.resume_package, ResumeOutput)
        assert isinstance(result.outreach_package, OutreachOutput)


# ============================================================
# Crew Test Mode Integration Tests
# ============================================================
class TestCrewTestMode:
    """Test the full crew workflow in test mode."""

    def test_crew_returns_package(self, sample_job: JobListing) -> None:
        """Full workflow returns CompleteApplicationPackage in test mode."""
        # Patch environment to avoid requiring real API keys
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

            from crews.job_search_crew import JobSearchCrew
            crew = JobSearchCrew(config)
            result = crew.run(sample_job, resume_profile=generate_mock_resume_profile())

        assert isinstance(result, CompleteApplicationPackage)

    def test_crew_no_llm_in_test_mode(self, sample_job: JobListing) -> None:
        """LLM should NOT be initialized in test mode."""
        env_patch = {
            "GROQ_API_KEY": "test-key",
            "USAJOBS_API_KEY": "test-key",
            "USAJOBS_EMAIL": "test@test.com",
            "TEST_MODE": "true",
        }
        with patch.dict(os.environ, env_patch):
            from utils.config import load_config
            config = load_config()

            from crews.job_search_crew import JobSearchCrew
            crew = JobSearchCrew(config)
            assert crew.llm is None
            assert crew.test_mode is True

    def test_crew_output_is_job_specific(self, sample_job: JobListing) -> None:
        """Mock outputs should reference the actual job details."""
        env_patch = {
            "GROQ_API_KEY": "test-key",
            "USAJOBS_API_KEY": "test-key",
            "USAJOBS_EMAIL": "test@test.com",
            "TEST_MODE": "true",
        }
        with patch.dict(os.environ, env_patch):
            from utils.config import load_config
            config = load_config()

            from crews.job_search_crew import JobSearchCrew
            crew = JobSearchCrew(config)
            result = crew.run(sample_job, resume_profile=generate_mock_resume_profile())

        # Verify job details appear in outputs
        assert "Data Scientist" in result.analysis.role_summary
        assert "Data Scientist" in result.resume_package.cover_letter
        assert "Data Scientist" in result.outreach_package.linkedin_message

    def test_crew_output_json_serializable(self, sample_job: JobListing) -> None:
        """Output must be JSON-serializable for SQLite storage."""
        env_patch = {
            "GROQ_API_KEY": "test-key",
            "USAJOBS_API_KEY": "test-key",
            "USAJOBS_EMAIL": "test@test.com",
            "TEST_MODE": "true",
        }
        with patch.dict(os.environ, env_patch):
            from utils.config import load_config
            config = load_config()

            from crews.job_search_crew import JobSearchCrew
            crew = JobSearchCrew(config)
            result = crew.run(sample_job, resume_profile=generate_mock_resume_profile())

        # Must serialize and deserialize cleanly
        json_str = result.model_dump_json()
        restored = CompleteApplicationPackage.model_validate_json(json_str)
        assert restored == result


# ============================================================
# Run standalone
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
