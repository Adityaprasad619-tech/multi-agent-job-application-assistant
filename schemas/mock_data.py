"""
Mock Data for Test Mode
========================
Deterministic mock outputs that mirror the exact Pydantic schema structure.

Design Decisions:
- Returns fully validated Pydantic objects — same types as the real workflow.
- Job-specific: interpolates the job title and organization into mock content
  so the mock outputs are visually distinguishable per job.
- Used by JobSearchCrew when config.test_mode is True.
- Zero external dependencies (no LLM, no network).
"""

from __future__ import annotations

from schemas.agent_outputs import (
    CompleteApplicationPackage,
    JobAnalysisOutput,
    OutreachOutput,
    ResumeOutput,
)
from schemas.resume_analysis import ResumeAnalysis
from schemas.ats_score import ATSScore, PartialMatch
from schemas.gap_analysis import GapAnalysis
from schemas.resume_profile import StructuredResumeProfile, ExperienceItem, ProjectItem
from services.usajobs_service import JobListing


def generate_mock_analysis(job: JobListing) -> JobAnalysisOutput:
    """Return a deterministic mock JobAnalysisOutput for the given job."""
    return JobAnalysisOutput(
        role_summary=(
            f"This is a {job.title} position at {job.organization} within the "
            f"{job.department}. The role involves technical responsibilities in "
            f"{job.location} with a salary range of ${job.salary_min}–${job.salary_max}."
        ),
        required_skills=[
            "Python",
            "SQL",
            "REST APIs",
            "Data Analysis",
            "Technical Documentation",
        ],
        preferred_skills=[
            "AWS",
            "Docker",
            "Kubernetes",
            "CI/CD Pipelines",
        ],
        ats_keywords=[
            "Python",
            "Cloud Computing",
            "Microservices",
            "Agile",
            "Data Engineering",
            job.title,
        ],
        experience_requirements=(
            "3+ years of professional experience in software development "
            "or a related technical field. Federal employment experience preferred."
        ),
    )


def generate_mock_resume(job: JobListing) -> ResumeOutput:
    """Return a deterministic mock ResumeOutput for the given job."""
    return ResumeOutput(
        professional_summary=(
            f"Results-driven professional with extensive experience in the skills "
            f"required for the {job.title} position at {job.organization}. Proven "
            f"track record of delivering high-quality technical solutions in fast-paced "
            f"environments. Seeking to leverage expertise to contribute to {job.department} "
            f"mission-critical initiatives."
        ),
        resume_recommendations=[
            f"Add a prominent 'Technical Skills' section listing Python, SQL, and REST APIs",
            f"Include a project demonstrating cloud deployment experience (AWS/Docker)",
            f"Quantify achievements with metrics (e.g., 'Reduced API latency by 40%')",
            f"Use the exact phrase '{job.title}' in your resume headline",
            f"Add a 'Relevant Coursework' or 'Certifications' section if applicable",
            f"Tailor your work experience bullets to mirror the job description language",
        ],
        cover_letter=(
            f"Dear Hiring Manager,\n\n"
            f"I am writing to express my strong interest in the {job.title} position "
            f"at {job.organization} ({job.department}). With my background in software "
            f"development and data analysis, I am confident in my ability to make a "
            f"meaningful contribution to your team.\n\n"
            f"Throughout my career, I have developed expertise in Python, REST APIs, "
            f"and cloud technologies — skills directly aligned with this role's requirements. "
            f"I am particularly drawn to {job.organization}'s mission and the opportunity "
            f"to work on impactful projects.\n\n"
            f"I would welcome the opportunity to discuss how my experience aligns with "
            f"your team's needs. Thank you for your time and consideration.\n\n"
            f"Sincerely,\n[Your Name]"
        ),
    )


def generate_mock_outreach(job: JobListing) -> OutreachOutput:
    """Return a deterministic mock OutreachOutput for the given job."""
    return OutreachOutput(
        linkedin_message=(
            f"Hi! I'm excited about the {job.title} role at {job.organization}. "
            f"I'd love to connect and learn more about the team."
        ),
        recruiter_message=(
            f"Subject: Interest in {job.title} — {job.organization}\n\n"
            f"Dear Recruiter,\n\n"
            f"I recently came across the {job.title} position at {job.organization} "
            f"and was immediately drawn to the role's focus on technical innovation "
            f"within {job.department}. With my experience in Python, REST APIs, and "
            f"cloud technologies, I believe I could contribute meaningfully to your team.\n\n"
            f"Would you be available for a brief call this week to discuss the position? "
            f"I'd appreciate any insights you could share about the role and team culture.\n\n"
            f"Best regards,\n[Your Name]"
        ),
        followup_message=(
            f"Hi,\n\n"
            f"I wanted to follow up on my message regarding the {job.title} position "
            f"at {job.organization}. I remain very interested in this opportunity and "
            f"have since completed a project involving microservices architecture that "
            f"I believe is directly relevant to your team's work.\n\n"
            f"I'd welcome the chance to connect at your convenience.\n\n"
            f"Best regards,\n[Your Name]"
        ),
    )


def generate_mock_resume_analysis() -> ResumeAnalysis:
    """Return a deterministic mock ResumeAnalysis."""
    return ResumeAnalysis(
        extracted_skills=["Python", "SQL", "REST APIs", "Git", "HTML/CSS"],
        strengths=["Strong backend programming foundations", "Experience building REST APIs"],
        weaknesses=["Lacks cloud computing experience", "No containerization technologies shown (Docker/Kubernetes)"],
        years_of_experience="3 years",
        education_summary="B.S. in Computer Science from State University",
    )


def generate_mock_gap_analysis() -> GapAnalysis:
    """Return a deterministic mock GapAnalysis."""
    return GapAnalysis(
        matching_skills=["Python", "SQL", "REST APIs"],
        missing_skills=["AWS", "Docker", "Kubernetes", "CI/CD Pipelines"],
        improvement_recommendations=[
            "Add Docker and AWS to your resume technical skills list.",
            "Illustrate a personal project where you built and deployed a Python service to AWS using a Docker container.",
        ],
    )


def generate_mock_ats_score() -> ATSScore:
    """Return a deterministic mock ATSScore."""
    return ATSScore(
        ats_score=60,
        matched_keywords=["Python", "SQL", "REST APIs"],
        partially_matched_keywords=[
            PartialMatch(
                required_skill="Data Analysis",
                matched_via=["pandas", "data analytics"],
            ),
        ],
        missing_keywords=["AWS", "Docker", "Kubernetes"],
        recommendations=[
            "Incorporate missing key technical keywords: AWS, Docker, Kubernetes.",
            "Add experience bullets showcasing data analysis pipelines built with Python.",
            "Strengthen partial matches by explicitly mentioning: Data Analysis. "
            "Your resume demonstrates related skills, but using the exact terminology will improve ATS pass rates.",
        ],
    )


def generate_mock_package(job: JobListing) -> CompleteApplicationPackage:
    """
    Generate a complete mock application package.

    This is the main entry point for test mode — returns the same
    CompleteApplicationPackage type as the real crew workflow.
    """
    return CompleteApplicationPackage(
        analysis=generate_mock_analysis(job),
        resume_package=generate_mock_resume(job),
        outreach_package=generate_mock_outreach(job),
        resume_analysis=generate_mock_resume_analysis(),
        ats_score=generate_mock_ats_score(),
        gap_analysis=generate_mock_gap_analysis(),
    )


def generate_mock_resume_profile() -> StructuredResumeProfile:
    """Return a deterministic mock StructuredResumeProfile."""
    return StructuredResumeProfile(
        full_name="John Doe",
        email="john.doe@example.com",
        phone="1-555-555-5555",
        linkedin_url="linkedin.com/in/johndoe",
        github_url="github.com/johndoe",
        location="Oklahoma City, OK",
        technical_skills=["Python", "SQL", "REST APIs", "Git", "HTML/CSS"],
        experience=[
            ExperienceItem(
                title="Software Engineer Intern",
                company="OKC Tech Solutions",
                summary="Wrote Python scripts to automate data entry, saving 5 hours of manual work weekly. Worked on Git-based version control with a team of 3 developers. Assisted in database schema design and querying using PostgreSQL.",
            )
        ],
        projects=[
            ProjectItem(
                name="Aviation Safety Monitor",
                technologies=["Python", "Git", "PostgreSQL"],
                summary="Developed a web application that collects and visualizes mock flight safety logs. Connected databases to generate automated warning signals.",
            )
        ],
        education=["B.S. in Computer Science - University of Oklahoma (2025)"],
        achievements=["Dean's List 2024", "First Place in Local Hackathon 2025"],
        certifications=["AWS Certified Cloud Practitioner (2025)", "Git Essentials Certification"],
    )

