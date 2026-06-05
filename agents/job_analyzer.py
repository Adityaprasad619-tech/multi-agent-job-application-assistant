"""
Job Analyzer Agent
===================
CrewAI agent that dissects a job posting to extract structured insights.

Design Decisions:
- Role/goal/backstory are the personality levers CrewAI uses to steer the LLM.
- Backstory is written as a professional bio to ground the agent's perspective.
- allow_delegation=False — V1 has no peer agents to delegate to.
- verbose=True — logs agent reasoning to console/logfile for debugging.
- LLM is injected (not created here) to honor single-source-of-truth in llm_service.
"""

from crewai import Agent, LLM


def create_job_analyzer_agent(llm: LLM) -> Agent:
    """
    Create and return the Job Analyzer agent.

    Parameters
    ----------
    llm : LLM
        The shared Groq LLM instance.

    Returns
    -------
    Agent
        A CrewAI agent configured for job posting analysis.
    """
    return Agent(
        role="Senior Job Posting Analyst",
        goal=(
            "Thoroughly analyze job postings to extract every relevant detail — "
            "required skills, preferred qualifications, ATS keywords, experience "
            "requirements, and a clear role summary — so that downstream agents "
            "can produce perfectly tailored application materials."
        ),
        backstory=(
            "You are a veteran technical recruiter with 15 years of experience "
            "in talent acquisition across federal agencies and Fortune 500 companies. "
            "You have deep expertise in Applicant Tracking Systems (ATS) and know "
            "exactly which keywords and phrases get resumes past automated screening. "
            "You read job postings with surgical precision, identifying both explicit "
            "requirements and implicit expectations that most candidates miss."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
