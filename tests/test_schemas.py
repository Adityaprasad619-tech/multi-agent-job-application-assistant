"""
Schema Validation Tests
========================
Validates all Pydantic models used by the agent workflow.

Tests:
- Valid data passes validation for all models.
- Missing required fields raise ValidationError.
- Incorrect types raise ValidationError.
- CompleteApplicationPackage correctly composes sub-models.
- JSON serialization/deserialization round-trips cleanly.

Run with:
    python -m pytest tests/test_schemas.py -v
    OR
    python tests/test_schemas.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

# Ensure project root is on sys.path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schemas.agent_outputs import (
    CompleteApplicationPackage,
    JobAnalysisOutput,
    OutreachOutput,
    ResumeOutput,
)


# ============================================================
# Fixtures
# ============================================================
@pytest.fixture
def valid_analysis() -> JobAnalysisOutput:
    return JobAnalysisOutput(
        role_summary="Backend engineering role focused on APIs and cloud systems.",
        required_skills=["Python", "REST APIs", "SQL"],
        preferred_skills=["AWS", "Docker"],
        ats_keywords=["Python", "Cloud", "Microservices"],
        experience_requirements="2+ years backend development experience",
    )


@pytest.fixture
def valid_resume() -> ResumeOutput:
    return ResumeOutput(
        professional_summary="Experienced engineer with strong Python and cloud skills.",
        resume_recommendations=[
            "Highlight API development experience",
            "Emphasize cloud deployment projects",
        ],
        cover_letter="Dear Hiring Manager,\n\nI am excited to apply...\n\nSincerely,\nJohn Doe",
    )


@pytest.fixture
def valid_outreach() -> OutreachOutput:
    return OutreachOutput(
        linkedin_message="Hi! I'm interested in the SWE role at your company.",
        recruiter_message="Dear Recruiter,\n\nI'd love to discuss the position...",
        followup_message="Hi, following up on my previous message...",
    )


# ============================================================
# JobAnalysisOutput
# ============================================================
class TestJobAnalysisOutput:
    def test_valid_creation(self, valid_analysis: JobAnalysisOutput) -> None:
        assert valid_analysis.role_summary.startswith("Backend")
        assert len(valid_analysis.required_skills) == 3
        assert len(valid_analysis.preferred_skills) == 2
        assert len(valid_analysis.ats_keywords) == 3
        assert "2+" in valid_analysis.experience_requirements

    def test_missing_required_field(self) -> None:
        with pytest.raises(ValidationError):
            JobAnalysisOutput(
                role_summary="Test",
                required_skills=["Python"],
                # missing: preferred_skills, ats_keywords, experience_requirements
            )

    def test_wrong_type_skills(self) -> None:
        with pytest.raises(ValidationError):
            JobAnalysisOutput(
                role_summary="Test",
                required_skills="not a list",  # should be list[str]
                preferred_skills=["AWS"],
                ats_keywords=["Python"],
                experience_requirements="2 years",
            )

    def test_json_roundtrip(self, valid_analysis: JobAnalysisOutput) -> None:
        json_str = valid_analysis.model_dump_json()
        restored = JobAnalysisOutput.model_validate_json(json_str)
        assert restored == valid_analysis

    def test_dict_roundtrip(self, valid_analysis: JobAnalysisOutput) -> None:
        data = valid_analysis.model_dump()
        restored = JobAnalysisOutput.model_validate(data)
        assert restored == valid_analysis


# ============================================================
# ResumeOutput
# ============================================================
class TestResumeOutput:
    def test_valid_creation(self, valid_resume: ResumeOutput) -> None:
        assert "engineer" in valid_resume.professional_summary.lower()
        assert len(valid_resume.resume_recommendations) == 2
        assert "Dear" in valid_resume.cover_letter

    def test_missing_cover_letter(self) -> None:
        with pytest.raises(ValidationError):
            ResumeOutput(
                professional_summary="Test",
                resume_recommendations=["Test recommendation"],
                # missing: cover_letter
            )

    def test_json_roundtrip(self, valid_resume: ResumeOutput) -> None:
        json_str = valid_resume.model_dump_json()
        restored = ResumeOutput.model_validate_json(json_str)
        assert restored == valid_resume


# ============================================================
# OutreachOutput
# ============================================================
class TestOutreachOutput:
    def test_valid_creation(self, valid_outreach: OutreachOutput) -> None:
        assert len(valid_outreach.linkedin_message) > 0
        assert len(valid_outreach.recruiter_message) > 0
        assert len(valid_outreach.followup_message) > 0

    def test_missing_followup(self) -> None:
        with pytest.raises(ValidationError):
            OutreachOutput(
                linkedin_message="Hi!",
                recruiter_message="Dear Recruiter...",
                # missing: followup_message
            )

    def test_json_roundtrip(self, valid_outreach: OutreachOutput) -> None:
        json_str = valid_outreach.model_dump_json()
        restored = OutreachOutput.model_validate_json(json_str)
        assert restored == valid_outreach


# ============================================================
# CompleteApplicationPackage
# ============================================================
class TestCompleteApplicationPackage:
    def test_valid_composition(
        self,
        valid_analysis: JobAnalysisOutput,
        valid_resume: ResumeOutput,
        valid_outreach: OutreachOutput,
    ) -> None:
        package = CompleteApplicationPackage(
            analysis=valid_analysis,
            resume_package=valid_resume,
            outreach_package=valid_outreach,
        )
        assert package.analysis.required_skills == ["Python", "REST APIs", "SQL"]
        assert len(package.resume_package.resume_recommendations) == 2
        assert "following up" in package.outreach_package.followup_message.lower()

    def test_json_roundtrip(
        self,
        valid_analysis: JobAnalysisOutput,
        valid_resume: ResumeOutput,
        valid_outreach: OutreachOutput,
    ) -> None:
        package = CompleteApplicationPackage(
            analysis=valid_analysis,
            resume_package=valid_resume,
            outreach_package=valid_outreach,
        )
        json_str = package.model_dump_json()
        restored = CompleteApplicationPackage.model_validate_json(json_str)
        assert restored == package

    def test_nested_access(
        self,
        valid_analysis: JobAnalysisOutput,
        valid_resume: ResumeOutput,
        valid_outreach: OutreachOutput,
    ) -> None:
        package = CompleteApplicationPackage(
            analysis=valid_analysis,
            resume_package=valid_resume,
            outreach_package=valid_outreach,
        )
        # Verify typed access through the composition
        assert isinstance(package.analysis, JobAnalysisOutput)
        assert isinstance(package.resume_package, ResumeOutput)
        assert isinstance(package.outreach_package, OutreachOutput)

    def test_missing_sub_model(self, valid_analysis: JobAnalysisOutput) -> None:
        with pytest.raises(ValidationError):
            CompleteApplicationPackage(
                analysis=valid_analysis,
                # missing: resume_package, outreach_package
            )


# ============================================================
# Run standalone
# ============================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
