import pytest
from unittest.mock import MagicMock, patch
import litellm

from crews.job_search_crew import parse_retry_after, JobSearchCrew
from tasks.analysis_tasks import format_profile_compact, format_profile_detailed
from schemas.resume_profile import StructuredResumeProfile, ExperienceItem, ProjectItem
from utils.config import AppConfig


def test_parse_retry_after():
    """Verify that parse_retry_after correctly extracts cooldown duration."""
    assert parse_retry_after("Rate limit exceeded: try again in 5.34s") == 5.34
    assert parse_retry_after("rate limit exceeded: try again in 23m5.2s") == 1385.2
    assert parse_retry_after("Please retry after 12 seconds") == 12.0
    assert parse_retry_after("wait 2.5 sec") == 2.5
    assert parse_retry_after("No rate limit message here") is None


def test_formatters():
    """Verify that compact and detailed formatters match requirements."""
    profile = StructuredResumeProfile(
        full_name="Alice Smith",
        email="alice@example.com",
        phone="123-456-7890",
        linkedin_url="linkedin.com/in/alice",
        github_url="github.com/alice",
        location="New York, NY",
        technical_skills=["Python", "SQL", "Machine Learning"],
        experience=[
            ExperienceItem(
                title="Data Scientist",
                company="Tech Corp",
                summary="Developed machine learning models for forecasting."
            )
        ],
        projects=[
            ProjectItem(
                name="Job Searcher",
                technologies=["Python", "Streamlit"],
                summary="AI job search tool."
            )
        ],
        education=["MS Data Science"],
        achievements=["Won best hackathon project"],
        certifications=["AWS Certified Cloud Practitioner"]
    )

    # Compact formatter: exclude identity/contact fields, summaries/descriptions
    compact_text = format_profile_compact(profile)
    assert "Alice Smith" not in compact_text
    assert "alice@example.com" not in compact_text
    assert "123-456-7890" not in compact_text
    assert "linkedin.com/in/alice" not in compact_text
    assert "github.com/alice" not in compact_text
    assert "New York, NY" not in compact_text
    assert "Developed machine learning models" not in compact_text
    assert "AI job search tool" not in compact_text
    assert "Python" in compact_text
    assert "MS Data Science" in compact_text
    assert "Won best hackathon project" in compact_text
    assert "AWS Certified Cloud Practitioner" in compact_text
    assert "Data Scientist at Tech Corp" in compact_text
    assert "Job Searcher" in compact_text

    # Detailed formatter: include all fields
    detailed_text = format_profile_detailed(profile)
    assert "Alice Smith" in detailed_text
    assert "alice@example.com" in detailed_text
    assert "123-456-7890" in detailed_text
    assert "Developed machine learning models" in detailed_text
    assert "AI job search tool" in detailed_text


@patch("crews.job_search_crew.Crew")
@patch("crews.job_search_crew.time.sleep")
def test_rate_limit_retry_loop(mock_sleep, mock_crew_class):
    """Verify that JobSearchCrew handles RateLimitError by retrying and calling callbacks."""
    # Mock config
    from pathlib import Path
    config = AppConfig(
        groq_api_key="mock_key",
        groq_model_name="llama-3.3-70b-versatile",
        usajobs_api_key="mock_key",
        usajobs_email="mock@example.com",
        auth_provider="local",
        clerk_secret_key="",
        clerk_publishable_key="",
        test_mode=False,
        project_root=Path("."),
        db_path=Path(":memory:"),
        log_dir=Path(".")
    )

    crew_instance = MagicMock()
    mock_crew_class.return_value = crew_instance

    # Make kickoff fail twice with rate limit message, then succeed
    mock_error = Exception("Groq rate limit exceeded: try again in 4.5s")
    
    # We want 2 failures then 1 success
    crew_instance.kickoff.side_effect = [mock_error, mock_error, None]

    # Mock job listing and resume profile
    from services.usajobs_service import JobListing
    job = JobListing(
        position_id="123",
        title="Software Engineer",
        organization="NASA",
        department="JPL",
        location="Pasadena, CA",
        salary_min="100000",
        salary_max="150000",
        pay_interval="Per Year",
        grade_low="12",
        grade_high="13",
        position_url="https://nasa.gov",
        open_date="2026-06-01",
        close_date="2026-06-30",
        description="Write code.",
        qualifications="Know python.",
        who_may_apply="US Citizens",
    )
    profile = StructuredResumeProfile(
        full_name="Alice",
        email="alice@example.com",
        technical_skills=["Python"],
        experience=[],
        projects=[],
        education=[],
        achievements=[],
        certifications=[]
    )

    # Initialize JobSearchCrew
    job_search_crew = JobSearchCrew(config)

    # Mock task outputs so _extract_output works
    from schemas.agent_outputs import JobAnalysisOutput, OutreachOutput, ResumeOutput
    from schemas.resume_analysis import ResumeAnalysis
    from schemas.gap_analysis import GapAnalysis

    # Mock tasks
    mock_task = MagicMock()
    mock_task.output.pydantic = JobAnalysisOutput(
        role_summary="Role",
        required_skills=["Python"],
        preferred_skills=[],
        ats_keywords=[],
        experience_requirements=""
    )
    
    mock_res_task = MagicMock()
    mock_res_task.output.pydantic = ResumeAnalysis(
        extracted_skills=["Python"],
        strengths=[],
        weaknesses=[],
        years_of_experience="2.0",
        education_summary=""
    )

    mock_gap_task = MagicMock()
    mock_gap_task.output.pydantic = GapAnalysis(
        matching_skills=["Python"],
        missing_skills=[],
        improvement_recommendations=[]
    )

    mock_resume_task = MagicMock()
    mock_resume_task.output.pydantic = ResumeOutput(
        professional_summary="",
        resume_recommendations=[],
        cover_letter=""
    )

    mock_outreach_task = MagicMock()
    mock_outreach_task.output.pydantic = OutreachOutput(
        linkedin_message="",
        recruiter_message="",
        followup_message=""
    )

    # We need to mock create_job_analysis_task and others or make them return tasks with mocked outputs
    with patch("crews.job_search_crew.create_job_analysis_task", return_value=mock_task), \
         patch("crews.job_search_crew.create_resume_analysis_task", return_value=mock_res_task), \
         patch("crews.job_search_crew.create_gap_analysis_task", return_value=mock_gap_task), \
         patch("crews.job_search_crew.create_resume_task", return_value=mock_resume_task), \
         patch("crews.job_search_crew.create_outreach_task", return_value=mock_outreach_task):
        
        retry_calls = []
        def on_retry_callback(attempt, wait_time, exception_message=None):
            retry_calls.append((attempt, wait_time))

        package = job_search_crew.run(job, profile, on_retry=on_retry_callback)

        # Asserts
        assert len(retry_calls) == 2
        # First retry (attempt 1) -> parsed wait time (4.5s)
        assert retry_calls[0] == (1, 4.5)
        # Second retry (attempt 2) -> 5.0s
        assert retry_calls[1] == (2, 5.0)

        # Verify sleep was called twice with the correct times
        mock_sleep.assert_any_call(4.5)
        mock_sleep.assert_any_call(5.0)
        assert mock_sleep.call_count == 2
