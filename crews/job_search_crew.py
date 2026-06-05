"""
Job Search Crew Orchestrator
==============================
Assembles agents and tasks into a sequential CrewAI workflow.

Design Decisions:
- Process.sequential — agents run one after another, each consuming prior outputs.
- Single LLM shared across all agents (created via services/llm_service.py).
- After kickoff, structured outputs are extracted from each task's `output.pydantic`
  and composed into a CompleteApplicationPackage.
- Error handling wraps the entire crew execution — if any agent fails, a clear
  error is raised with context about which step failed.
"""

from __future__ import annotations

import re
import time
import litellm
from crewai import Crew, Process
from loguru import logger

from agents.job_analyzer import create_job_analyzer_agent
from agents.outreach_specialist import create_outreach_specialist_agent
from agents.resume_specialist import create_resume_specialist_agent
from agents.resume_gap_analyst import create_resume_gap_analyst_agent

from schemas.agent_outputs import (
    CompleteApplicationPackage,
    JobAnalysisOutput,
    OutreachOutput,
    ResumeOutput,
)
from schemas.resume_analysis import ResumeAnalysis
from schemas.ats_score import ATSScore
from schemas.gap_analysis import GapAnalysis
from schemas.resume_profile import StructuredResumeProfile
from schemas.mock_data import generate_mock_package

from services.llm_service import create_llm
from services.usajobs_service import JobListing
from services.ats_service import ATSService
from services.skill_normalizer import normalize_skills
from tasks.analysis_tasks import (
    create_job_analysis_task,
    create_resume_analysis_task,
    create_gap_analysis_task,
    create_resume_task,
    create_outreach_task,
)
from utils.config import AppConfig


def parse_retry_after(exception_msg: str) -> float | None:
    """Parse retry-after/wait duration from exception message."""
    msg_lower = exception_msg.lower()
    
    # Pattern: "try again in X.Y s" or "try again in Xs" or similar
    match = re.search(r'try again in\s+([\d\.]+)\s*s', msg_lower)
    if match:
        return float(match.group(1))
        
    # Pattern: "try again in Xm Ys" or "try again in XmYs"
    match = re.search(r'try again in\s+(\d+)m\s*([\d\.]*)s?', msg_lower)
    if match:
        m = int(match.group(1))
        s = float(match.group(2)) if match.group(2) else 0.0
        return m * 60 + s

    # Pattern: "retry after X seconds"
    match = re.search(r'retry after\s+([\d\.]+)\s*sec', msg_lower)
    if match:
        return float(match.group(1))
        
    # Pattern: "wait X seconds" or "wait X.Y seconds"
    match = re.search(r'wait\s+([\d\.]+)\s*sec', msg_lower)
    if match:
        return float(match.group(1))
        
    return None


class JobSearchCrew:
    """
    Orchestrates the multi-agent job application workflow.

    Workflow:
        Job Analyzer → Resume Gap Analyst → Resume Specialist → Outreach Specialist
    """

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize the crew with a shared LLM.

        Parameters
        ----------
        config : AppConfig
            Application configuration containing Groq API key and model name.
        """
        self.config = config
        self.test_mode = config.test_mode

        if self.test_mode:
            self.llm = None
            logger.info("JobSearchCrew initialized in TEST MODE — no Groq calls")
        else:
            self.llm = create_llm(
                api_key=config.groq_api_key,
                model_name=config.groq_model_name,
            )
            logger.info(
                "JobSearchCrew initialized — model={}",
                config.groq_model_name,
            )

    def run(
        self,
        job: JobListing,
        resume_profile: StructuredResumeProfile,
        on_retry: callable | None = None,
    ) -> CompleteApplicationPackage:
        """
        Execute the full agent workflow for a selected job listing and candidate resume profile.

        Parameters
        ----------
        job : JobListing
            The job to analyze and generate materials for.
        resume_profile : StructuredResumeProfile
            The candidate's structured resume profile.
        on_retry : callable, optional
            A callback function that accepts (attempt, wait_time) when a rate limit retry occurs.

        Returns
        -------
        CompleteApplicationPackage
            Combined structured output from all agents.

        Raises
        ------
        RuntimeError
            If the crew execution fails or outputs cannot be parsed.
        """
        logger.info(
            "Starting crew workflow for: {} at {}",
            job.title,
            job.organization,
        )

        # --- Test Mode: return mock outputs immediately ---
        if self.test_mode:
            logger.info("TEST MODE — returning mock outputs (no Groq API calls)")
            return generate_mock_package(job)

        # --- Create Agents ---
        analyzer_agent = create_job_analyzer_agent(self.llm)
        gap_analyst_agent = create_resume_gap_analyst_agent(self.llm)
        resume_agent = create_resume_specialist_agent(self.llm)
        outreach_agent = create_outreach_specialist_agent(self.llm)

        # --- Create Tasks (with context chaining) ---
        analysis_task = create_job_analysis_task(
            agent=analyzer_agent,
            job=job,
        )
        resume_analysis_task = create_resume_analysis_task(
            agent=gap_analyst_agent,
            resume_profile=resume_profile,
        )
        gap_analysis_task = create_gap_analysis_task(
            agent=gap_analyst_agent,
            resume_profile=resume_profile,
            analysis_task=analysis_task,
        )
        resume_task = create_resume_task(
            agent=resume_agent,
            job=job,
            resume_profile=resume_profile,
            analysis_task=analysis_task,
            gap_analysis_task=gap_analysis_task,
        )
        outreach_task = create_outreach_task(
            agent=outreach_agent,
            job=job,
            resume_profile=resume_profile,
            analysis_task=analysis_task,
            resume_task=resume_task,
        )

        # --- Assemble Crew ---
        crew = Crew(
            agents=[analyzer_agent, gap_analyst_agent, resume_agent, outreach_agent],
            tasks=[
                analysis_task,
                resume_analysis_task,
                gap_analysis_task,
                resume_task,
                outreach_task,
            ],
            process=Process.sequential,
            verbose=True,
        )

        # --- Execute with Rate Limit Resilience ---
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info("Kicking off crew execution (attempt {}/{})...", attempt, max_attempts)
                crew.kickoff()
                logger.info("Crew execution completed successfully.")
                break
            except Exception as exc:
                exc_msg = str(exc)
                is_rate_limit = (
                    isinstance(exc, litellm.RateLimitError) or
                    "rate limit" in exc_msg.lower() or
                    "429" in exc_msg
                )
                if is_rate_limit and attempt < max_attempts:
                    wait_time = 3.0
                    if attempt == 1:
                        parsed = parse_retry_after(exc_msg)
                        if parsed is not None:
                            wait_time = parsed
                        else:
                            wait_time = 3.0
                    elif attempt == 2:
                        wait_time = 5.0
                    elif attempt == 3:
                        wait_time = 10.0

                    logger.warning(
                        "Rate limit detected. Attempt {}/{} failed. Retrying in {:.2f}s...",
                        attempt, max_attempts, wait_time
                    )

                    if on_retry:
                        try:
                            on_retry(attempt, wait_time, exc_msg)
                        except Exception as cb_exc:
                            logger.error("Error in on_retry callback: {}", cb_exc)

                    time.sleep(wait_time)
                else:
                    logger.error("Crew execution failed on final attempt {}/{}: {}", attempt, max_attempts, exc)
                    raise RuntimeError(
                        f"AI workflow failed during execution: {exc}"
                    ) from exc

        # --- Extract Structured Outputs ---
        try:
            analysis_output = self._extract_output(
                analysis_task, JobAnalysisOutput, "Job Analysis"
            )
            resume_analysis_output = self._extract_output(
                resume_analysis_task, ResumeAnalysis, "Resume Analysis"
            )
            gap_analysis_output = self._extract_output(
                gap_analysis_task, GapAnalysis, "Gap Analysis"
            )
            resume_output = self._extract_output(
                resume_task, ResumeOutput, "Resume & Cover Letter"
            )
            outreach_output = self._extract_output(
                outreach_task, OutreachOutput, "Outreach"
            )
        except Exception as exc:
            logger.error("Failed to extract structured outputs: {}", exc)
            raise RuntimeError(
                f"AI workflow completed but output parsing failed: {exc}"
            ) from exc

        # --- Token Tracking & Application-Layer Logging ---
        try:
            # 1. Job Analyzer
            job_prompt = len(analysis_task.description)
            job_prompt_tokens = int(job_prompt / 4)
            job_resp_tokens = int(len(str(analysis_output)) / 4)

            # 2. Resume Analysis
            res_prompt = len(resume_analysis_task.description)
            res_prompt_tokens = int(res_prompt / 4)
            res_resp_tokens = int(len(str(resume_analysis_output)) / 4)

            # 3. Gap Analysis (includes job analysis context)
            gap_prompt = len(gap_analysis_task.description) + len(str(analysis_output))
            gap_prompt_tokens = int(gap_prompt / 4)
            gap_resp_tokens = int(len(str(gap_analysis_output)) / 4)

            # 4. Resume Specialist (includes job and gap analysis context)
            spec_prompt = len(resume_task.description) + len(str(analysis_output)) + len(str(gap_analysis_output))
            spec_prompt_tokens = int(spec_prompt / 4)
            spec_resp_tokens = int(len(str(resume_output)) / 4)

            # 5. Outreach Specialist (includes job and resume specialist context)
            out_prompt = len(outreach_task.description) + len(str(analysis_output)) + len(str(resume_output))
            out_prompt_tokens = int(out_prompt / 4)
            out_resp_tokens = int(len(str(outreach_output)) / 4)

            # Logging per agent
            logger.info("Job Analyzer completed.\nPrompt Tokens ≈ {}\n", job_prompt_tokens)
            logger.info("Resume Analysis completed.\nPrompt Tokens ≈ {}\n", res_prompt_tokens)
            logger.info("Gap Analysis completed.\nPrompt Tokens ≈ {}\n", gap_prompt_tokens)
            logger.info("Resume Specialist completed.\nPrompt Tokens ≈ {}\n", spec_prompt_tokens)
            logger.info("Outreach completed.\nPrompt Tokens ≈ {}\n", out_prompt_tokens)

            # Workflow-level summary
            total_prompt_tokens = job_prompt_tokens + res_prompt_tokens + gap_prompt_tokens + spec_prompt_tokens + out_prompt_tokens
            total_resp_tokens = job_resp_tokens + res_resp_tokens + gap_resp_tokens + spec_resp_tokens + out_resp_tokens
            total_workflow_tokens = total_prompt_tokens + total_resp_tokens

            summary_log = (
                "\n================ WORKFLOW TOKEN SUMMARY ================\n"
                f"1. Job Analyzer:\n"
                f"   - Prompt Size: {job_prompt} chars (~{job_prompt_tokens} tokens)\n"
                f"   - Estimated Agent Usage: ~{job_prompt_tokens + job_resp_tokens} tokens\n"
                f"2. Resume Analysis:\n"
                f"   - Prompt Size: {res_prompt} chars (~{res_prompt_tokens} tokens)\n"
                f"   - Estimated Agent Usage: ~{res_prompt_tokens + res_resp_tokens} tokens\n"
                f"3. Gap Analysis:\n"
                f"   - Prompt Size: {gap_prompt} chars (~{gap_prompt_tokens} tokens)\n"
                f"   - Estimated Agent Usage: ~{gap_prompt_tokens + gap_resp_tokens} tokens\n"
                f"4. Resume Specialist:\n"
                f"   - Prompt Size: {spec_prompt} chars (~{spec_prompt_tokens} tokens)\n"
                f"   - Estimated Agent Usage: ~{spec_prompt_tokens + spec_resp_tokens} tokens\n"
                f"5. Outreach Specialist:\n"
                f"   - Prompt Size: {out_prompt} chars (~{out_prompt_tokens} tokens)\n"
                f"   - Estimated Agent Usage: ~{out_prompt_tokens + out_resp_tokens} tokens\n"
                "--------------------------------------------------------\n"
                f"TOTAL ESTIMATED WORKFLOW TOKEN USAGE: ~{total_workflow_tokens} tokens\n"
                "========================================================"
            )
            logger.info(summary_log)
        except Exception as log_err:
            logger.debug("Failed to calculate and log token usage details: {}", log_err)

        # --- Normalize Skills Before ATS Scoring ---

        # --- Normalize Skills Before ATS Scoring ---
        raw_required = analysis_output.required_skills
        logger.info("ATS Input — Raw required_skills ({}): {}", len(raw_required), raw_required)
        normalized_required = normalize_skills(raw_required)
        logger.info("ATS Input — Normalized required_skills ({}): {}", len(normalized_required), normalized_required)

        # Also normalize preferred skills for consistency
        raw_preferred = analysis_output.preferred_skills
        normalized_preferred = normalize_skills(raw_preferred)

        # Update the analysis output with normalized skills
        analysis_output = JobAnalysisOutput(
            role_summary=analysis_output.role_summary,
            required_skills=normalized_required,
            preferred_skills=normalized_preferred,
            ats_keywords=analysis_output.ats_keywords,
            experience_requirements=analysis_output.experience_requirements,
        )

        # --- Calculate ATS Match Score Deterministically ---
        try:
            ats_score_output = ATSService.calculate_match(
                resume_profile=resume_profile,
                required_skills=normalized_required,
            )
        except Exception as exc:
            logger.error("Deterministic ATS scoring failed: {}", exc)
            # Safe fallback if ATS calculation crashes
            ats_score_output = ATSScore(
                ats_score=50,
                matched_keywords=[],
                missing_keywords=normalized_required,
                recommendations=["Failed to calculate score. Tailor based on job keywords."],
            )

        package = CompleteApplicationPackage(
            analysis=analysis_output,
            resume_package=resume_output,
            outreach_package=outreach_output,
            resume_analysis=resume_analysis_output,
            ats_score=ats_score_output,
            gap_analysis=gap_analysis_output,
        )

        logger.info(
            "Application package generated — {} required skills, "
            "{} recommendations, {} ATS score",
            len(package.analysis.required_skills),
            len(package.resume_package.resume_recommendations),
            package.ats_score.ats_score if package.ats_score else "N/A",
        )

        return package

    @staticmethod
    def _extract_output(task, model_class: type, step_name: str):
        """
        Extract a Pydantic model from a completed task's output.

        Tries task.output.pydantic first (CrewAI native),
        falls back to parsing the raw text as JSON.

        Parameters
        ----------
        task : Task
            The completed CrewAI task.
        model_class : type
            The Pydantic model class to validate against.
        step_name : str
            Human-readable name for error messages.

        Returns
        -------
        BaseModel
            Validated Pydantic model instance.
        """
        output = task.output
        if output is None:
            raise ValueError(f"Task '{step_name}' did not produce any output.")

        # Path 1: CrewAI already parsed into Pydantic
        if hasattr(output, "pydantic") and output.pydantic is not None:
            logger.debug("{} — extracted via output.pydantic", step_name)
            return output.pydantic

        # Path 2: Try parsing the raw text as JSON
        if hasattr(output, "json_dict") and output.json_dict is not None:
            logger.debug("{} — extracted via output.json_dict", step_name)
            return model_class.model_validate(output.json_dict)

        # Path 3: Parse raw string
        raw = str(output.raw) if hasattr(output, "raw") else str(output)
        logger.debug("{} — attempting to parse raw text as JSON", step_name)
        return model_class.model_validate_json(raw)
