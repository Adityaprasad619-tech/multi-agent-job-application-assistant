"""
Skill Normalizer
==================
Deterministic utility that converts verbose requirement sentences from
job postings into concise, ATS-ready skill labels.

Root Cause Context:
  The Job Analyzer LLM often returns requirement phrases like:
    "Experience with coding or algorithm development, including Python and SQL"
  instead of concise labels like:
    ["Programming", "Python", "SQL"]

  The ATS taxonomy engine cannot match full sentences against skill categories.
  This normalizer bridges that gap.

Design Decisions:
- Fully deterministic: no LLM, no embeddings.
- Reusable by ATS Engine, Gap Analysis, Resume Tailoring, and future systems.
- Two-pass strategy:
    1. Extract known technologies/skills by scanning against the taxonomy.
    2. Map remaining preamble phrases to abstract competency labels.
- Preserves already-clean skill labels (passthrough for short, clean inputs).
"""

from __future__ import annotations

import re
from loguru import logger
from services.skill_taxonomy import SKILL_TAXONOMY, REVERSE_SKILL_INDEX


# ==================================================================
# PREAMBLE PATTERNS TO STRIP
# ==================================================================
# These prefixes appear in verbose requirement sentences and should be
# removed before skill extraction.
# ==================================================================

_PREAMBLE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^experience\s+(with|in|using|working\s+with)\s+", re.IGNORECASE),
    re.compile(r"^ability\s+to\s+", re.IGNORECASE),
    re.compile(r"^knowledge\s+of\s+", re.IGNORECASE),
    re.compile(r"^proficiency\s+(in|with)\s+", re.IGNORECASE),
    re.compile(r"^familiarity\s+with\s+", re.IGNORECASE),
    re.compile(r"^understanding\s+of\s+", re.IGNORECASE),
    re.compile(r"^demonstrated\s+(ability|experience|knowledge)\s+(to|in|of|with)\s+", re.IGNORECASE),
    re.compile(r"^strong\s+(background|skills?|experience)\s+(in|with)\s+", re.IGNORECASE),
    re.compile(r"^proven\s+(ability|track\s+record|experience)\s+(to|in|of|with)\s+", re.IGNORECASE),
    re.compile(r"^must\s+have\s+", re.IGNORECASE),
    re.compile(r"^requires?\s+", re.IGNORECASE),
    re.compile(r"^bachelor'?s?\s+degree\s+in\s+", re.IGNORECASE),
    re.compile(r"^master'?s?\s+degree\s+in\s+", re.IGNORECASE),
    re.compile(r"^degree\s+in\s+", re.IGNORECASE),
    re.compile(r"^minimum\s+of\s+\d+\s+years?\s+(of\s+)?", re.IGNORECASE),
    re.compile(r"^\d+\+?\s+years?\s+(of\s+)?(experience\s+(in|with)\s+)?", re.IGNORECASE),
]

# ==================================================================
# PHRASE-TO-SKILL MAPPING
# ==================================================================
# Maps common verbose phrases found inside requirement sentences to
# concise skill labels. Applied AFTER preamble stripping.
# ==================================================================

_PHRASE_TO_SKILL: dict[str, str] = {
    "coding or algorithm development": "Programming",
    "coding": "Programming",
    "algorithm development": "Algorithm Design",
    "algorithm design": "Algorithm Design",
    "quantitative data": "Quantitative Analysis",
    "quantitative analysis": "Quantitative Analysis",
    "analyzing and interpreting quantitative data": "Quantitative Analysis",
    "analyzing and interpreting data": "Data Analysis",
    "scientific modeling systems": "Scientific Modeling",
    "scientific modeling": "Scientific Modeling",
    "statistical or predictive analysis": "Statistical Analysis",
    "statistical analysis": "Statistical Analysis",
    "predictive analysis": "Predictive Analysis",
    "predictive modeling": "Predictive Modeling",
    "data analysis": "Data Analysis",
    "data analytics": "Data Analysis",
    "data management": "Data Management",
    "database management": "Database Management",
    "software development": "Software Development",
    "software engineering": "Software Engineering",
    "web development": "Web Development",
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "artificial intelligence": "Artificial Intelligence",
    "cloud computing": "Cloud Computing",
    "project management": "Project Management",
    "technical writing": "Technical Writing",
    "technical documentation": "Technical Documentation",
    "problem solving": "Problem Solving",
    "critical thinking": "Critical Thinking",
    "analytical thinking": "Analytical Thinking",
    "team collaboration": "Team Collaboration",
    "working collaboratively": "Team Collaboration",
    "collaboratively as part of a team": "Team Collaboration",
    "working as part of a team": "Team Collaboration",
    "work independently": "Independent Work",
    "oral and written communication": "Communication",
    "written and oral communication": "Communication",
    "communication skills": "Communication",
    "interpersonal skills": "Interpersonal Skills",
    "geospatial analysis": "Geospatial Analysis",
    "remote sensing": "Remote Sensing",
    "geographic information systems": "GIS",
    "gis": "GIS",
}

# ==================================================================
# TECHNOLOGY EXTRACTION PATTERNS
# ==================================================================
# Common delimiters used in requirement sentences to list technologies.
# ==================================================================

_TECH_DELIMITERS = re.compile(
    r"(?:,\s*|\s+and\s+|\s+or\s+|\s+and/or\s+|;\s*|\s*/\s*)",
    re.IGNORECASE,
)

# Build a set of all known skills/technologies for fast lookup
_ALL_KNOWN_SKILLS: set[str] = set()
for _cat in SKILL_TAXONOMY:
    _ALL_KNOWN_SKILLS.add(_cat)
    for _syn in SKILL_TAXONOMY[_cat]:
        _ALL_KNOWN_SKILLS.add(_syn.lower())


def _strip_preamble(text: str) -> str:
    """Remove known preamble phrases from a requirement sentence."""
    result = text.strip()
    for pattern in _PREAMBLE_PATTERNS:
        result = pattern.sub("", result).strip()
    # Remove trailing period
    result = result.rstrip(".")
    return result


def _extract_technologies(text: str) -> list[str]:
    """
    Scan text for known technology names from the taxonomy.
    Returns list of matched technology/skill names (original casing from taxonomy).
    """
    text_lower = text.lower()
    found: list[str] = []

    # Check longer phrases first to avoid partial matches
    # (e.g., "machine learning" before "machine")
    all_skills_sorted = sorted(_ALL_KNOWN_SKILLS, key=len, reverse=True)

    for skill in all_skills_sorted:
        # Use word boundary matching to avoid partial matches
        escaped = re.escape(skill)
        pattern = rf"(?<![a-zA-Z]){escaped}(?![a-zA-Z])"
        if re.search(pattern, text_lower):
            # Don't add duplicates
            if skill not in [s.lower() for s in found]:
                found.append(skill)

    return found


def _extract_phrase_skills(text: str) -> list[str]:
    """
    Map known verbose phrases to concise skill labels.
    Checked against _PHRASE_TO_SKILL mapping.
    """
    text_lower = text.lower()
    found: list[str] = []

    # Sort by phrase length (longest first) to match most specific phrases
    sorted_phrases = sorted(_PHRASE_TO_SKILL.keys(), key=len, reverse=True)

    for phrase in sorted_phrases:
        if phrase in text_lower:
            label = _PHRASE_TO_SKILL[phrase]
            if label not in found:
                found.append(label)

    return found


def _looks_like_sentence(text: str) -> bool:
    """
    Heuristic to detect if a skill string is a verbose requirement sentence
    rather than a concise skill label.

    Returns True if the text:
    - Exceeds 40 characters, OR
    - Contains preamble-like phrases, OR
    - Contains multiple commas (listing pattern), OR
    - Starts with common sentence starters
    """
    if len(text) > 40:
        return True
    text_lower = text.lower().strip()
    sentence_starters = [
        "experience ", "ability to ", "knowledge of ", "proficiency ",
        "familiarity ", "understanding of ", "demonstrated ",
        "strong ", "proven ", "must have ", "require", "bachelor",
        "master", "degree in ", "minimum ",
    ]
    for starter in sentence_starters:
        if text_lower.startswith(starter):
            return True
    if text.count(",") >= 2:
        return True
    return False


def normalize_skill(raw_skill: str) -> list[str]:
    """
    Normalize a single raw skill string into one or more concise skill labels.

    If the input is already a clean skill label (short, no preamble), it is
    returned as-is in a single-element list.

    If the input is a verbose requirement sentence, it is decomposed into:
    - Extracted technology names (Python, SQL, etc.)
    - Mapped abstract competencies (Statistical Analysis, Programming, etc.)

    Parameters
    ----------
    raw_skill : str
        A single skill entry from the Job Analyzer's required_skills list.

    Returns
    -------
    list[str]
        One or more normalized, concise skill labels.
    """
    raw_skill = raw_skill.strip()
    if not raw_skill:
        return []

    # Fast path: already a clean label
    if not _looks_like_sentence(raw_skill):
        return [raw_skill]

    # Strip preamble
    stripped = _strip_preamble(raw_skill)

    # Extract known technologies
    techs = _extract_technologies(stripped)

    # Extract phrase-based skill mappings
    phrase_skills = _extract_phrase_skills(stripped)

    # Also try to extract technologies that may be in a comma/or/and list
    # within the sentence (e.g., "including Fortran, C/C++, IDL, R, Python")
    # Split on "including" or "such as" to get the technology list portion
    including_match = re.search(
        r"(?:including|such as|e\.g\.|like)\s+(.+)$",
        stripped,
        re.IGNORECASE,
    )
    if including_match:
        tech_portion = including_match.group(1)
        fragments = _TECH_DELIMITERS.split(tech_portion)
        for frag in fragments:
            frag_clean = frag.strip().rstrip(".")
            if frag_clean and len(frag_clean) <= 30:
                # Check if it's a known skill
                if frag_clean.lower() in _ALL_KNOWN_SKILLS:
                    if frag_clean not in techs and frag_clean.lower() not in [t.lower() for t in techs]:
                        techs.append(frag_clean)
                elif len(frag_clean) <= 20:
                    # Short fragment — likely a technology name even if not in taxonomy
                    # e.g., "Fortran", "IDL", "GNSS"
                    if frag_clean not in techs and frag_clean not in phrase_skills:
                        techs.append(frag_clean)

    # Combine results, deduplicating
    combined: list[str] = []
    seen_lower: set[str] = set()

    for skill in phrase_skills:
        if skill.lower() not in seen_lower:
            combined.append(skill)
            seen_lower.add(skill.lower())

    for tech in techs:
        # Capitalize known taxonomy entries properly
        if tech.lower() not in seen_lower:
            # Use title case for multi-word, preserve single-word casing
            if tech.islower() and " " not in tech:
                combined.append(tech.upper() if len(tech) <= 3 else tech.capitalize())
            else:
                combined.append(tech)
            seen_lower.add(tech.lower())

    # If we found nothing, return the stripped text as a single label
    if not combined:
        # Truncate to something reasonable
        label = stripped[:60].strip()
        if label:
            combined.append(label)

    return combined


def normalize_skills(raw_skills: list[str]) -> list[str]:
    """
    Normalize a list of raw skill strings into a flat list of concise skill labels.

    This is the main entry point for normalizing the Job Analyzer's output
    before feeding it to the ATS engine, Gap Analysis, or Resume Tailoring.

    Parameters
    ----------
    raw_skills : list[str]
        Raw required_skills list from the Job Analyzer agent.

    Returns
    -------
    list[str]
        Flattened, deduplicated list of normalized skill labels.
    """
    normalized: list[str] = []
    seen_lower: set[str] = set()

    for raw in raw_skills:
        labels = normalize_skill(raw)
        for label in labels:
            if label.lower() not in seen_lower:
                normalized.append(label)
                seen_lower.add(label.lower())

    logger.info(
        "Skill normalization: {} raw → {} normalized",
        len(raw_skills),
        len(normalized),
    )

    return normalized
