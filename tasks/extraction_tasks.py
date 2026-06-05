"""
Resume Extraction Tasks
========================
Task factory for the resume profile extraction phase.
"""

from __future__ import annotations
from crewai import Agent, Task
from schemas.resume_profile import StructuredResumeProfile


def create_profile_extraction_task(
    agent: Agent,
    resume_text: str,
) -> Task:
    """
    Create the task responsible for extracting StructuredResumeProfile.

    Parameters
    ----------
    agent : Agent
        The Resume Profile Extractor agent.
    resume_text : str
        The raw extracted text of the user's resume.

    Returns
    -------
    Task
        A CrewAI task that produces StructuredResumeProfile.
    """
    description = f"""Analyze the candidate's raw resume text and extract all details, including identity/contact details and career history, into a structured profile.

## Candidate's Resume Text:
{resume_text}

## Your Task
1. Identity & Contact Information: Extract the candidate's personal information if present:
   - full_name: The candidate's full name.
   - email: The candidate's email address.
   - phone: The candidate's phone number.
   - linkedin_url: The URL of the candidate's LinkedIn profile (do not invent).
   - github_url: The URL of the candidate's GitHub profile (do not invent).
   - location: The candidate's city, state, or location.
   If any of these fields are not present in the resume text, leave them as null. Do NOT fabricate or guess them.
2. Technical Skills: Extract all core technical skills, programming languages, libraries, databases, and methodologies.
3. Experience: Extract every job/role. For each role, provide:
   - title: Job Title
   - company: Company/Organization name
   - summary: Concise description of duties, projects, and achievements in that specific role.
4. Projects: Extract notable personal or professional projects. For each, provide:
   - name: Project name
   - technologies: List of technologies/tools used in that project
   - summary: Brief description of goals and outcomes.
5. Education: Extract degrees, majors, colleges/universities, and graduation years.
6. Achievements: Extract key professional accolades, awards, publications, or measurable career metrics.
7. Certifications: Extract all professional certifications, credentials, licenses, or course completion badges.

Return your output as a highly structured JSON matching the StructuredResumeProfile schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with full_name, email, phone, linkedin_url, github_url, location, "
            "technical_skills, experience (list of objects with title, company, summary), "
            "projects (list of objects with name, technologies, summary), education, achievements, and certifications."
        ),
        agent=agent,
        output_pydantic=StructuredResumeProfile,
    )
