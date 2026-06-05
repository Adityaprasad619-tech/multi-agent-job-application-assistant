"""
Resume Profile Extractor Agent
=============================
Defines the agent responsible for extracting a structured, token-efficient
resume profile from raw resume text.
"""

from __future__ import annotations
from crewai import Agent, LLM


def create_profile_extractor_agent(llm: LLM) -> Agent:
    """
    Create and return the Resume Profile Extractor agent.

    Parameters
    ----------
    llm : LLM
        The shared Groq LLM instance.

    Returns
    -------
    Agent
        The configured CrewAI Agent.
    """
    return Agent(
        role="Senior Resume Profile Extractor",
        goal=(
            "Analyze candidate raw resume text to extract their contact details, name, and a complete, structured, "
            "and token-efficient profile containing technical skills, work experience, "
            "academic education, key projects, accomplishments, and professional certifications."
        ),
        backstory=(
            "You are an expert ATS integration specialist and professional data architect. "
            "Your domain expertise is converting unformatted or verbose resume texts into clean, "
            "fully structured, and normalized profiles. You excel at extracting candidate names, contact details "
            "(email, phone, LinkedIn, GitHub, location), precise achievements, "
            "technologies, and role details without altering or losing critical credentials."
        ),
        verbose=True,
        allow_delegation=False,
        llm=llm,
    )
