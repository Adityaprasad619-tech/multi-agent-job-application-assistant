"""
LLM Service
============
Factory for the Groq-backed LLM used by all CrewAI agents.

Design Decisions:
- Single factory function so the model config is defined in one place.
- Uses langchain-groq ChatGroq, which CrewAI natively supports.
- Temperature kept low (0.3) for deterministic, professional outputs.
- Easy to swap models by changing GROQ_MODEL_NAME in .env.
"""

import crewai.llms.cache
from crewai import LLM
from loguru import logger

# Disable CrewAI prompt caching breakpoints globally to prevent compatibility issues
# with Groq (which throws errors when 'cache_breakpoint' is present in system/role messages).
crewai.llms.cache.mark_cache_breakpoint = lambda message: message


def create_llm(api_key: str, model_name: str) -> LLM:
    """
    Create and return a CrewAI LLM instance.

    Parameters
    ----------
    api_key : str
        Groq API key.
    model_name : str
        Model identifier (e.g. 'llama-3.3-70b-versatile').

    Returns
    -------
    LLM
        Ready-to-use LLM for CrewAI agents.
    """
    logger.info("Initializing Groq LLM — model={}", model_name)

    # CrewAI utilizes LiteLLM under the hood, which requires a provider prefix
    formatted_model = model_name
    if not formatted_model.startswith("groq/"):
        formatted_model = f"groq/{formatted_model}"

    # Design Decision: max_tokens = 1500 is the smallest safe value.
    # This ensures that long cover letters (300-400 words) and resume recommendations
    # can be fully generated without truncating, while preventing runaway costs.
    llm = LLM(
        model=formatted_model,
        api_key=api_key,
        temperature=0.3,
        max_tokens=1500,
    )

    return llm

