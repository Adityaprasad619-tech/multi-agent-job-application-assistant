"""
Agent Initialization Tests
===========================
Verifies that the LLM service and all four agents (Job Analyzer,
Resume Specialist, Resume Gap Analyst, and Outreach Specialist)
can be instantiated without Pydantic validation or wiring errors.
"""

from __future__ import annotations

import pytest
from services.llm_service import create_llm
from agents.job_analyzer import create_job_analyzer_agent
from agents.resume_specialist import create_resume_specialist_agent
from agents.resume_gap_analyst import create_resume_gap_analyst_agent
from agents.outreach_specialist import create_outreach_specialist_agent
from agents.resume_profile_extractor import create_profile_extractor_agent


def test_llm_and_agents_initialization():
    """Verify that LLM creation and agent initialization succeed."""
    # Given
    mock_api_key = "gsk_test_api_key_for_wiring_validation"
    model_name = "llama-3.3-70b-versatile"

    # When (LLM instantiation)
    llm = create_llm(api_key=mock_api_key, model_name=model_name)

    # Then (LLM properties)
    assert llm is not None
    assert llm.model == "groq/llama-3.3-70b-versatile"
    assert llm.api_key == mock_api_key

    # When & Then (Agent instantiations)
    job_analyzer = create_job_analyzer_agent(llm)
    assert job_analyzer is not None
    assert job_analyzer.role == "Senior Job Posting Analyst"
    assert job_analyzer.llm == llm

    resume_specialist = create_resume_specialist_agent(llm)
    assert resume_specialist is not None
    assert resume_specialist.role == "Senior Resume & Cover Letter Specialist"
    assert resume_specialist.llm == llm

    gap_analyst = create_resume_gap_analyst_agent(llm)
    assert gap_analyst is not None
    assert gap_analyst.role == "Senior Resume Gap Analyst"
    assert gap_analyst.llm == llm

    outreach_specialist = create_outreach_specialist_agent(llm)
    assert outreach_specialist is not None
    assert outreach_specialist.role == "Senior Networking & Outreach Specialist"
    assert outreach_specialist.llm == llm

    profile_extractor = create_profile_extractor_agent(llm)
    assert profile_extractor is not None
    assert profile_extractor.role == "Senior Resume Profile Extractor"
    assert profile_extractor.llm == llm
