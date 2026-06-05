"""
Resume Gap Analyst Agent
========================
CrewAI agent that compares a candidate's resume with a job posting to perform a gap analysis.
"""

from __future__ import annotations

from crewai import Agent, LLM


def create_resume_gap_analyst_agent(llm: LLM) -> Agent:
    """
    Create and return the Resume Gap Analyst agent.

    Parameters
    ----------
    llm : LLM
        The shared Groq LLM instance.

    Returns
    -------
    Agent
        A CrewAI agent configured for resume gap analysis.
    """
    return Agent(
        role="Senior Resume Gap Analyst",
        goal=(
            "Compare the candidate's parsed resume text against the job requirements "
            "provided by the Job Analyzer. Perform a comprehensive gap analysis "
            "to identify matching skills, critical missing skills/keywords, and "
            "provide highly detailed, actionable recommendations for resume improvement."
        ),
        backstory=(
            "You are a technical career coach and skills auditor with 10 years of "
            "experience in conducting career transition analysis and resume audits. "
            "You excel at examining a candidate's profile side-by-side with a complex "
            "job description to identify matching strengths and critical missing competencies. "
            "Your professional, constructive advice helps candidates fill skills gaps "
            "effectively before submitting applications."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
