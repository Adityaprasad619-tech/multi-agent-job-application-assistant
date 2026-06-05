"""
ATS Match Scoring Service
==========================
Calculates a deterministic, reproducible ATS match score using:
1. Direct keyword matching (exact substring match, case-insensitive)
2. Synonym/taxonomy matching (skill normalization via skill_taxonomy)

Scoring Formula:
    score = ((direct_matches + 0.8 * partial_matches) / total_required) * 100

Design Decisions:
- Direct matches count as 1.0 weight (exact keyword found in resume text).
- Partial/synonym matches count as 0.8 weight (resume contains a related
  technology that satisfies the requirement via taxonomy mapping).
- A requirement matched directly is NOT also counted as partial.
- Fully deterministic: same inputs → same score, always.
- No LLM calls, no embeddings, no fuzzy/semantic matching.
"""

from __future__ import annotations

import re
from loguru import logger
from schemas.ats_score import ATSScore, PartialMatch
from schemas.resume_profile import StructuredResumeProfile
from services.skill_taxonomy import (
    SKILL_TAXONOMY,
    REVERSE_SKILL_INDEX,
    get_synonyms_for_category,
)


# Weight applied to partial (synonym/taxonomy) matches in score calculation
PARTIAL_MATCH_WEIGHT = 0.8


class ATSService:
    """Deterministic ATS matching engine with skill normalization."""

    @staticmethod
    def _extract_resume_skills(resume_profile: StructuredResumeProfile | str) -> tuple[str, set[str]]:
        """
        Extract unified text and discrete skill tokens from the resume input.

        Returns
        -------
        tuple[str, set[str]]
            (lowercased unified text, set of lowercased discrete skill tokens)
        """
        if isinstance(resume_profile, str):
            return resume_profile.lower(), set()

        text_parts: list[str] = []
        discrete_skills: set[str] = set()

        # Technical skills are both discrete tokens and text
        for skill in resume_profile.technical_skills:
            discrete_skills.add(skill.lower().strip())
            text_parts.append(skill)

        for exp in resume_profile.experience:
            text_parts.append(exp.title)
            text_parts.append(exp.company)
            text_parts.append(exp.summary)

        for proj in resume_profile.projects:
            text_parts.append(proj.name)
            for tech in proj.technologies:
                discrete_skills.add(tech.lower().strip())
                text_parts.append(tech)
            text_parts.append(proj.summary)

        text_parts.extend(resume_profile.education)
        text_parts.extend(resume_profile.achievements)
        text_parts.extend(resume_profile.certifications)

        unified_text = " ".join(text_parts).lower()
        return unified_text, discrete_skills

    @staticmethod
    def calculate_match(
        resume_profile: StructuredResumeProfile | str,
        required_skills: list[str],
    ) -> ATSScore:
        """
        Compare resume against required skills using direct + taxonomy matching.

        Scoring tiers:
        - DIRECT: The exact required keyword appears in the resume text → weight 1.0
        - PARTIAL: The resume contains a synonym/related technology → weight 0.8
        - MISSING: Neither direct nor taxonomy match found → weight 0.0

        Parameters
        ----------
        resume_profile : StructuredResumeProfile | str
            The candidate's structured resume profile or raw text.
        required_skills : list[str]
            List of required skills/keywords parsed from the job description.

        Returns
        -------
        ATSScore
            Validated score with direct matches, partial matches, and missing keywords.
        """
        logger.info("Starting ATS match calculation with {} required skills", len(required_skills))

        if not required_skills:
            logger.warning("Required skills list is empty. Defaulting ATS score to 100.")
            return ATSScore(
                ats_score=100,
                matched_keywords=[],
                partially_matched_keywords=[],
                missing_keywords=[],
                recommendations=[
                    "The job description does not list explicit technical requirements. Resume is well aligned."
                ],
            )

        unified_text, discrete_skills = ATSService._extract_resume_skills(resume_profile)

        direct_matched: list[str] = []
        partial_matched: list[PartialMatch] = []
        missing: list[str] = []

        for skill in required_skills:
            skill_clean = skill.strip()
            if not skill_clean:
                continue

            # --- Phase 1: Direct exact match ---
            escaped = re.escape(skill_clean.lower())
            if re.search(escaped, unified_text):
                direct_matched.append(skill_clean)
                continue

            # --- Phase 2: Taxonomy/synonym match ---
            # Strategy A: The required skill is a category — check if the resume
            # contains any of its known synonyms/technologies.
            skill_lower = skill_clean.lower()
            synonyms = get_synonyms_for_category(skill_lower)
            matched_synonyms: list[str] = []

            if synonyms:
                for synonym in synonyms:
                    syn_escaped = re.escape(synonym.lower())
                    if re.search(syn_escaped, unified_text):
                        matched_synonyms.append(synonym)

            # Strategy B: Check if any discrete resume skill maps to a category
            # that the required skill also belongs to or matches.
            if not matched_synonyms:
                for resume_skill in discrete_skills:
                    # Does this resume skill have taxonomy parents?
                    parents = REVERSE_SKILL_INDEX.get(resume_skill, set())
                    if skill_lower in parents:
                        matched_synonyms.append(resume_skill)
                    # Also check if the required skill is a known synonym of any
                    # category that the resume skill also belongs to
                    elif parents:
                        for parent in parents:
                            parent_syns = SKILL_TAXONOMY.get(parent, [])
                            if skill_lower in [s.lower() for s in parent_syns]:
                                matched_synonyms.append(resume_skill)
                                break

            if matched_synonyms:
                # Deduplicate and limit to top 5 for readability
                unique_synonyms = list(dict.fromkeys(matched_synonyms))[:5]
                partial_matched.append(
                    PartialMatch(
                        required_skill=skill_clean,
                        matched_via=unique_synonyms,
                    )
                )
            else:
                missing.append(skill_clean)

        # --- Score Calculation ---
        total = len(direct_matched) + len(partial_matched) + len(missing)
        if total == 0:
            score = 100
        else:
            weighted = len(direct_matched) + (PARTIAL_MATCH_WEIGHT * len(partial_matched))
            raw_score = (weighted / total) * 100
            score = int(round(raw_score))
            score = max(0, min(100, score))

        # --- Recommendations ---
        recommendations: list[str] = []

        if missing:
            recommendations.append(
                f"Incorporate missing key technical keywords: {', '.join(missing[:5])}."
            )
            for skill in missing[:3]:
                recommendations.append(
                    f"Add a brief bullet point under your experience illustrating your exposure to '{skill}'."
                )

        if partial_matched:
            partial_names = [p.required_skill for p in partial_matched[:3]]
            recommendations.append(
                f"Strengthen partial matches by explicitly mentioning: {', '.join(partial_names)}. "
                f"Your resume demonstrates related skills, but using the exact terminology will improve ATS pass rates."
            )

        if not missing and not partial_matched:
            recommendations.append(
                "Excellent! Your resume highlights all key required technical terms."
            )

        logger.info(
            "ATS score calculated: {}% ({} direct, {} partial, {} missing)",
            score, len(direct_matched), len(partial_matched), len(missing),
        )

        return ATSScore(
            ats_score=score,
            matched_keywords=direct_matched,
            partially_matched_keywords=partial_matched,
            missing_keywords=missing,
            recommendations=recommendations,
        )
