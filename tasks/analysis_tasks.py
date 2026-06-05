"""
Analysis Tasks
================
Task factory for the job search workflow.

Design Decisions:
- Each function creates one Task with a specific prompt, agent, and output schema.
- Prompts include the job details inline.
- `output_pydantic` forces CrewAI to parse the LLM response into the Pydantic model.
- `context` parameter chains tasks: Task 2 sees Task 1's output, Task 3 sees both.
- Prompts explicitly instruct the LLM to return JSON matching the schema.
"""

from __future__ import annotations

from datetime import datetime
from crewai import Agent, Task

from schemas.agent_outputs import JobAnalysisOutput, OutreachOutput, ResumeOutput
from schemas.resume_analysis import ResumeAnalysis
from schemas.gap_analysis import GapAnalysis
from schemas.resume_profile import StructuredResumeProfile
from services.usajobs_service import JobListing


def format_profile_to_text(profile: StructuredResumeProfile) -> str:
    """Format the structured resume profile into a clean, compact text block for LLM prompts."""
    lines = []
    lines.append("## Candidate's Structured Resume Profile")
    if getattr(profile, "full_name", None):
        lines.append(f"- **Full Name:** {profile.full_name}")
    if getattr(profile, "email", None):
        lines.append(f"- **Email:** {profile.email}")
    if getattr(profile, "phone", None):
        lines.append(f"- **Phone:** {profile.phone}")
    if getattr(profile, "linkedin_url", None):
        lines.append(f"- **LinkedIn:** {profile.linkedin_url}")
    if getattr(profile, "github_url", None):
        lines.append(f"- **GitHub:** {profile.github_url}")
    if getattr(profile, "location", None):
        lines.append(f"- **Location:** {profile.location}")

    lines.append(f"- **Technical Skills:** {', '.join(profile.technical_skills) if profile.technical_skills else 'None listed'}")

    lines.append("- **Professional Experience:**")
    if profile.experience:
        for exp in profile.experience:
            lines.append(f"  * {exp.title} at {exp.company}: {exp.summary}")
    else:
        lines.append("  * None listed")

    lines.append("- **Key Projects:**")
    if profile.projects:
        for proj in profile.projects:
            techs = f" (Technologies: {', '.join(proj.technologies)})" if proj.technologies else ""
            lines.append(f"  * {proj.name}{techs}: {proj.summary}")
    else:
        lines.append("  * None listed")

    lines.append(f"- **Academic Education:** {'; '.join(profile.education) if profile.education else 'None listed'}")
    lines.append(f"- **Achievements:** {'; '.join(profile.achievements) if profile.achievements else 'None listed'}")
    lines.append(f"- **Certifications:** {'; '.join(profile.certifications) if profile.certifications else 'None listed'}")

    return "\n".join(lines)


def format_profile_compact(profile: StructuredResumeProfile) -> str:
    """Format structured resume profile into a highly compact text block excluding contact info and summaries."""
    lines = []
    lines.append("## Candidate's Compact Profile")
    # Exclude name, email, phone, linkedin, github, location
    lines.append(f"- **Technical Skills:** {', '.join(profile.technical_skills) if profile.technical_skills else 'None listed'}")

    lines.append("- **Experience (Titles & Companies only):**")
    if profile.experience:
        for exp in profile.experience:
            lines.append(f"  * {exp.title} at {exp.company}")
    else:
        lines.append("  * None listed")

    lines.append("- **Projects (Names only):**")
    if profile.projects:
        for proj in profile.projects:
            lines.append(f"  * {proj.name}")
    else:
        lines.append("  * None listed")

    lines.append(f"- **Education:** {'; '.join(profile.education) if profile.education else 'None listed'}")
    lines.append(f"- **Achievements:** {'; '.join(profile.achievements) if profile.achievements else 'None listed'}")
    lines.append(f"- **Certifications:** {'; '.join(profile.certifications) if profile.certifications else 'None listed'}")
    return "\n".join(lines)


def format_profile_detailed(profile: StructuredResumeProfile) -> str:
    """Format structured resume profile into a detailed text block including contact info and full summaries."""
    lines = []
    lines.append("## Candidate's Detailed Profile")
    if getattr(profile, "full_name", None):
        lines.append(f"- **Full Name:** {profile.full_name}")
    if getattr(profile, "email", None):
        lines.append(f"- **Email:** {profile.email}")
    if getattr(profile, "phone", None):
        lines.append(f"- **Phone:** {profile.phone}")
    if getattr(profile, "linkedin_url", None):
        lines.append(f"- **LinkedIn:** {profile.linkedin_url}")
    if getattr(profile, "github_url", None):
        lines.append(f"- **GitHub:** {profile.github_url}")
    if getattr(profile, "location", None):
        lines.append(f"- **Location:** {profile.location}")

    lines.append(f"- **Technical Skills:** {', '.join(profile.technical_skills) if profile.technical_skills else 'None listed'}")

    lines.append("- **Professional Experience:**")
    if profile.experience:
        for exp in profile.experience:
            lines.append(f"  * {exp.title} at {exp.company}: {exp.summary}")
    else:
        lines.append("  * None listed")

    lines.append("- **Key Projects:**")
    if profile.projects:
        for proj in profile.projects:
            techs = f" (Technologies: {', '.join(proj.technologies)})" if proj.technologies else ""
            lines.append(f"  * {proj.name}{techs}: {proj.summary}")
    else:
        lines.append("  * None listed")

    lines.append(f"- **Academic Education:** {'; '.join(profile.education) if profile.education else 'None listed'}")
    lines.append(f"- **Achievements:** {'; '.join(profile.achievements) if profile.achievements else 'None listed'}")
    lines.append(f"- **Certifications:** {'; '.join(profile.certifications) if profile.certifications else 'None listed'}")
    return "\n".join(lines)


def create_resume_analysis_task(
    agent: Agent,
    resume_profile: StructuredResumeProfile,
) -> Task:
    """Create the standalone resume analysis task using compact profile."""
    profile_text = format_profile_compact(resume_profile)
    description = f"""Analyze the candidate's compact profile to extract key insights.

{profile_text}

## Your Task
1. Extract all technical and soft skills (extracted_skills).
2. Identify 3-4 professional strengths (strengths).
3. Identify 2-3 potential gaps/weaknesses (weaknesses).
4. Summarize total years of experience (years_of_experience).
5. Summarize academic/education background (education_summary).

Return your output as structured JSON matching the ResumeAnalysis schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with keys: extracted_skills, strengths, "
            "weaknesses, years_of_experience, education_summary."
        ),
        agent=agent,
        output_pydantic=ResumeAnalysis,
    )


def create_job_analysis_task(
    agent: Agent,
    job: JobListing,
) -> Task:
    """Create the job analysis task with output constraints."""
    description = f"""Analyze this federal job posting:

- **Title:** {job.title}
- **Organization:** {job.organization}
- **Department:** {job.department}
- **Location:** {job.location}
- **Grade:** {job.grade_low} – {job.grade_high}
- **Salary:** ${job.salary_min} – ${job.salary_max} ({job.pay_interval})

## Job Description
{job.description}

## Qualifications
{job.qualifications}

## Your Task
1. Write a role summary (maximum 150 words).
2. Extract required skills as concise labels (1-3 words each, e.g., 'Python', 'SQL'). Do NOT return sentences or paragraphs.
3. Extract preferred skills as concise labels.
4. Extract ATS keywords as a list.
5. Summarize experience requirements.

Return your analysis as structured JSON matching the JobAnalysisOutput schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with keys: role_summary, required_skills, "
            "preferred_skills, ats_keywords, experience_requirements."
        ),
        agent=agent,
        output_pydantic=JobAnalysisOutput,
    )


def create_gap_analysis_task(
    agent: Agent,
    resume_profile: StructuredResumeProfile,
    analysis_task: Task,
) -> Task:
    """Create the resume gap analysis task using compact profile and output constraints."""
    profile_text = format_profile_compact(resume_profile)
    description = f"""Compare the candidate's compact profile with the Job Analysis context.

{profile_text}

## Your Task
1. Identify up to 5 key matching skills (matching_skills).
2. Identify up to 5 key missing/weak skills (missing_skills).
3. Provide up to 5 actionable improvement recommendations (improvement_recommendations).

Return as structured JSON matching the GapAnalysis schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with keys: matching_skills, missing_skills, "
            "improvement_recommendations."
        ),
        agent=agent,
        output_pydantic=GapAnalysis,
        context=[analysis_task],
    )


def create_resume_task(
    agent: Agent,
    job: JobListing,
    resume_profile: StructuredResumeProfile,
    analysis_task: Task,
    gap_analysis_task: Task,
) -> Task:
    """Create the tailored resume & cover letter task using detailed profile and output constraints."""
    profile_text = format_profile_detailed(resume_profile)
    current_date = datetime.now().strftime("%B %d, %Y")
    contact_lines = []
    if getattr(resume_profile, "full_name", None):
        contact_lines.append(resume_profile.full_name)
    if getattr(resume_profile, "email", None):
        contact_lines.append(resume_profile.email)
    if getattr(resume_profile, "phone", None):
        contact_lines.append(resume_profile.phone)
    if getattr(resume_profile, "linkedin_url", None):
        contact_lines.append(resume_profile.linkedin_url)
    if getattr(resume_profile, "github_url", None):
        contact_lines.append(resume_profile.github_url)

    contact_header = "\n".join(contact_lines) if contact_lines else ""
    header_block = f"{contact_header}\n\n{current_date}\n\nHiring Manager\n{job.organization}\n\nDear Hiring Manager,"

    description = f"""Use the Job Analysis and Gap Analysis context to craft tailored application materials.

{profile_text}

## Your Task
1. **Professional Summary:** Write a 3-4 sentence professional summary tailored to this position.
2. **Resume Recommendations:** Provide exactly 5 to 7 specific, actionable recommendations to tailor the resume.
3. **Cover Letter:** Write a 3-4 paragraph cover letter (300-400 words maximum).
   The `cover_letter` text field MUST start with the following header block:
   {header_block}

   Ensure the cover letter is professional, highlights matching skills, integrates ATS keywords, and stays under 400 words. Do NOT generate placeholders or make up facts.

Return as structured JSON matching the ResumeOutput schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with keys: professional_summary, "
            "resume_recommendations, cover_letter."
        ),
        agent=agent,
        output_pydantic=ResumeOutput,
        context=[analysis_task, gap_analysis_task],
    )


def create_outreach_task(
    agent: Agent,
    job: JobListing,
    resume_profile: StructuredResumeProfile,
    analysis_task: Task,
    resume_task: Task,
) -> Task:
    """Create the outreach task using compact profile and output constraints."""
    profile_text = format_profile_compact(resume_profile)
    description = f"""Generate personalized networking messages using context.

{profile_text}

## Your Task
1. **LinkedIn Message:** Write a connection message under 300 characters. Personalize with candidate name: {resume_profile.full_name or '[Applicant Name]'}.
2. **Recruiter Email:** Write a professional email (100-150 words). Personalize with candidate details:
   - Full Name: {resume_profile.full_name or '[Applicant Name]'}
   - Education: {', '.join(resume_profile.education) if resume_profile.education else '[Education]'}
   - Skills: {', '.join(resume_profile.technical_skills[:3]) if resume_profile.technical_skills else '[Skills]'}
   - Contact Info: Email: {resume_profile.email or '[Email]'}, Phone: {resume_profile.phone or '[Phone]'}
3. **Follow-Up Message:** Write a follow-up message (75-100 words) to send 5-7 days later if no response.

Do NOT generate fake information or placeholders. Return as structured JSON matching the OutreachOutput schema."""

    return Task(
        description=description,
        expected_output=(
            "A JSON object with keys: linkedin_message, "
            "recruiter_message, followup_message."
        ),
        agent=agent,
        output_pydantic=OutreachOutput,
        context=[analysis_task, resume_task],
    )

