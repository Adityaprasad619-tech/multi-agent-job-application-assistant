"""
Resume & Cover Letter Specialist Agent
========================================
CrewAI agent that generates tailored resume advice and cover letters.

Design Decisions:
- Consumes output from the Job Analyzer agent (passed via task context).
- Backstory emphasizes career coaching expertise to produce actionable,
  specific advice rather than generic templates.
- Focus on ATS compatibility since federal job applications are heavily screened.
"""

from crewai import Agent, LLM


def create_resume_specialist_agent(llm: LLM) -> Agent:
    """
    Create and return the Resume & Cover Letter Specialist agent.

    Parameters
    ----------
    llm : LLM
        The shared Groq LLM instance.

    Returns
    -------
    Agent
        A CrewAI agent configured for resume and cover letter generation.
    """
    return Agent(
        role="Senior Resume & Cover Letter Specialist",
        goal=(
            "Using the job analysis provided by the Job Analyzer, craft a compelling "
            "professional summary, actionable resume tailoring recommendations, and "
            "a polished cover letter that maximizes the candidate's chances of passing "
            "ATS screening and impressing hiring managers."
        ),
        backstory=(
            "You are a certified professional resume writer (CPRW) with 12 years of "
            "experience helping candidates land roles at federal agencies and top-tier "
            "tech companies. You specialize in translating job requirements into "
            "powerful resume bullet points and cover letters that tell a candidate's "
            "story while hitting every keyword the ATS is looking for. Your cover "
            "letters have a 40% higher interview callback rate than the industry average."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
