"""
Networking & Outreach Specialist Agent
========================================
CrewAI agent that generates professional networking messages.

Design Decisions:
- Consumes output from both Job Analyzer and Resume Specialist (via task context).
- Backstory emphasizes LinkedIn recruiting expertise for authentic messaging tone.
- Messages are short and actionable — optimized for real-world use on LinkedIn/email.
"""

from crewai import Agent, LLM


def create_outreach_specialist_agent(llm: LLM) -> Agent:
    """
    Create and return the Networking & Outreach Specialist agent.

    Parameters
    ----------
    llm : LLM
        The shared Groq LLM instance.

    Returns
    -------
    Agent
        A CrewAI agent configured for generating networking messages.
    """
    return Agent(
        role="Senior Networking & Outreach Specialist",
        goal=(
            "Generate professional, personalized networking messages — a LinkedIn "
            "connection request, a recruiter outreach email, and a follow-up message — "
            "that reference the specific role and demonstrate genuine interest and "
            "relevant qualifications without sounding generic or pushy."
        ),
        backstory=(
            "You are a career networking strategist who has helped over 2,000 "
            "professionals build meaningful connections on LinkedIn and land interviews "
            "through cold outreach. You understand the psychology of recruiters and "
            "hiring managers — what makes them open a message, what makes them respond, "
            "and what gets ignored. Your messages are warm, specific, and always include "
            "a clear call to action. You never use clichés like 'I hope this finds you well'."
        ),
        llm=llm,
        allow_delegation=False,
        verbose=True,
    )
