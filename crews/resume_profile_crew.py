from __future__ import annotations

import re
import time
import litellm
from crewai import Crew, Process
from loguru import logger

from agents.resume_profile_extractor import create_profile_extractor_agent
from tasks.extraction_tasks import create_profile_extraction_task
from schemas.resume_profile import StructuredResumeProfile
from schemas.mock_data import generate_mock_resume_profile
from services.llm_service import create_llm
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


class ResumeProfileCrew:
    """
    Orchestrates the lightweight resume profile extraction workflow.
    """

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.test_mode = config.test_mode

        if self.test_mode:
            self.llm = None
            logger.info("ResumeProfileCrew initialized in TEST MODE — no Groq calls")
        else:
            self.llm = create_llm(
                api_key=config.groq_api_key,
                model_name=config.groq_model_name,
            )
            logger.info(
                "ResumeProfileCrew initialized — model={}",
                config.groq_model_name,
            )

    def run(self, resume_text: str, on_retry: callable | None = None) -> StructuredResumeProfile:
        """
        Execute the profile extraction crew on raw resume text.
        """
        if self.test_mode:
            logger.info("TEST MODE — returning mock resume profile")
            return generate_mock_resume_profile()

        # --- Create Agent ---
        extractor_agent = create_profile_extractor_agent(self.llm)

        # --- Create Task ---
        extraction_task = create_profile_extraction_task(
            agent=extractor_agent,
            resume_text=resume_text,
        )

        # --- Assemble Crew ---
        crew = Crew(
            agents=[extractor_agent],
            tasks=[extraction_task],
            process=Process.sequential,
            verbose=True,
        )

        # --- Execute with Rate Limit Resilience ---
        max_attempts = 4
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info("Kicking off resume profile extraction crew (attempt {}/{})...", attempt, max_attempts)
                crew.kickoff()
                logger.info("Resume profile extraction crew completed successfully.")
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
                        "Rate limit detected in extraction. Attempt {}/{} failed. Retrying in {:.2f}s...",
                        attempt, max_attempts, wait_time
                    )

                    if on_retry:
                        try:
                            on_retry(attempt, wait_time, exc_msg)
                        except Exception as cb_exc:
                            logger.error("Error in on_retry callback: {}", cb_exc)

                    time.sleep(wait_time)
                else:
                    logger.error("Resume profile extraction crew failed on final attempt {}/{}: {}", attempt, max_attempts, exc)
                    raise RuntimeError(
                        f"Resume profile extraction failed during execution: {exc}"
                    ) from exc

        # --- Extract Pydantic Output ---
        try:
            output = extraction_task.output
            if output is None:
                raise ValueError("Extraction task did not produce output.")

            if hasattr(output, "pydantic") and output.pydantic is not None:
                profile_out = output.pydantic
            elif hasattr(output, "json_dict") and output.json_dict is not None:
                profile_out = StructuredResumeProfile.model_validate(output.json_dict)
            else:
                raw = str(output.raw) if hasattr(output, "raw") else str(output)
                profile_out = StructuredResumeProfile.model_validate_json(raw)

            # --- Token Tracking & Application-Layer Logging ---
            try:
                prompt_size = len(extraction_task.description)
                prompt_tokens = int(prompt_size / 4)
                resp_tokens = int(len(str(profile_out)) / 4)
                
                logger.info("Resume Profile Extractor completed.\nPrompt Tokens ≈ {}\n", prompt_tokens)
                
                summary_log = (
                    "\n================ EXTRACTION TOKEN SUMMARY ================\n"
                    f"1. Resume Profile Extractor:\n"
                    f"   - Prompt Size: {prompt_size} chars (~{prompt_tokens} tokens)\n"
                    f"   - Estimated Agent Usage: ~{prompt_tokens + resp_tokens} tokens\n"
                    "=========================================================="
                )
                logger.info(summary_log)
            except Exception as log_err:
                logger.debug("Failed to calculate extraction tokens: {}", log_err)

            return profile_out
        except Exception as exc:
            logger.error("Failed to parse StructuredResumeProfile: {}", exc)
            raise RuntimeError(
                f"Profile extraction succeeded but parsing failed: {exc}"
            ) from exc

