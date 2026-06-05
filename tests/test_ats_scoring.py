"""
ATS Match Scoring Tests
========================
Tests for ATSService.
Verifies scoring logic, case-insensitivity, recommendations, boundary values,
synonym/taxonomy matching, partial match scoring, and backward compatibility.
"""

from __future__ import annotations

import unittest
from services.ats_service import ATSService
from schemas.ats_score import ATSScore, PartialMatch
from schemas.resume_profile import StructuredResumeProfile, ExperienceItem, ProjectItem


class TestATSDirectMatching(unittest.TestCase):
    """Test suite for direct (exact) keyword matching — backward compatible."""

    def test_calculate_match_perfect(self) -> None:
        """Verify perfect score when all skills match directly."""
        resume = "Experienced software engineer with deep Python, SQL, and Docker skills."
        required = ["Python", "SQL", "Docker"]

        result = ATSService.calculate_match(resume, required)

        self.assertEqual(result.ats_score, 100)
        self.assertEqual(len(result.matched_keywords), 3)
        self.assertEqual(len(result.missing_keywords), 0)
        self.assertEqual(len(result.partially_matched_keywords), 0)

    def test_calculate_match_partial(self) -> None:
        """Verify score calculation is accurate on partial keyword overlap (direct only)."""
        resume = "Experienced software engineer with deep Python and SQL skills."
        required = ["Python", "SQL", "Docker", "AWS"]

        result = ATSService.calculate_match(resume, required)

        # 2 direct out of 4 = 50%
        self.assertEqual(result.ats_score, 50)
        self.assertEqual(set(result.matched_keywords), {"Python", "SQL"})
        self.assertIn("Docker", result.missing_keywords)
        self.assertIn("AWS", result.missing_keywords)

    def test_calculate_match_case_insensitive(self) -> None:
        """Verify matching is case insensitive."""
        resume = "experienced software developer with python, sql, and aws."
        required = ["PYTHON", "Sql", "AWS"]

        result = ATSService.calculate_match(resume, required)

        self.assertEqual(result.ats_score, 100)
        self.assertEqual(len(result.matched_keywords), 3)

    def test_calculate_match_empty_required(self) -> None:
        """Verify fallback when required skills are missing."""
        resume = "Some resume text."
        required = []

        result = ATSService.calculate_match(resume, required)

        self.assertEqual(result.ats_score, 100)
        self.assertEqual(len(result.matched_keywords), 0)
        self.assertTrue(len(result.recommendations) > 0)

    def test_calculate_match_zero_matches(self) -> None:
        """Verify score of 0% when no skills overlap at all."""
        resume = "Expert in GNSS and WGS84 coordinate systems."
        required = ["Python", "SQL"]

        result = ATSService.calculate_match(resume, required)

        self.assertEqual(result.ats_score, 0)
        self.assertEqual(len(result.matched_keywords), 0)
        self.assertEqual(len(result.missing_keywords), 2)


class TestATSSynonymMatching(unittest.TestCase):
    """Test suite for taxonomy/synonym-based matching."""

    def test_pandas_matches_statistical_analysis(self) -> None:
        """Resume with 'Pandas' should partially match 'Statistical Analysis'."""
        profile = StructuredResumeProfile(
            technical_skills=["Python", "Pandas", "NumPy"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Statistical Analysis"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.partially_matched_keywords), 1)
        self.assertEqual(result.partially_matched_keywords[0].required_skill, "Statistical Analysis")
        self.assertTrue(
            any("pandas" in v.lower() for v in result.partially_matched_keywords[0].matched_via)
        )
        self.assertEqual(len(result.missing_keywords), 0)
        # Partial match at 0.8 weight: 0.8/1 * 100 = 80%
        self.assertEqual(result.ats_score, 80)

    def test_scikit_learn_matches_machine_learning(self) -> None:
        """Resume with 'Scikit-Learn' should partially match 'Machine Learning'."""
        profile = StructuredResumeProfile(
            technical_skills=["Python", "Scikit-Learn"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Machine Learning"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.partially_matched_keywords), 1)
        self.assertEqual(result.partially_matched_keywords[0].required_skill, "Machine Learning")
        self.assertEqual(len(result.missing_keywords), 0)

    def test_sql_matches_database_management(self) -> None:
        """Resume with 'SQL' should partially match 'Database Management'."""
        profile = StructuredResumeProfile(
            technical_skills=["SQL", "PostgreSQL"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Database Management"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.partially_matched_keywords), 1)
        self.assertEqual(result.partially_matched_keywords[0].required_skill, "Database Management")
        self.assertEqual(len(result.missing_keywords), 0)

    def test_python_matches_coding(self) -> None:
        """Resume with 'Python' should partially match 'Coding'."""
        profile = StructuredResumeProfile(
            technical_skills=["Python"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Coding"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.partially_matched_keywords), 1)
        self.assertEqual(result.partially_matched_keywords[0].required_skill, "Coding")
        self.assertEqual(len(result.missing_keywords), 0)


class TestATSMixedMatching(unittest.TestCase):
    """Test suite for mixed direct + synonym matching scenarios."""

    def test_user_example_scenario(self) -> None:
        """
        The exact user-reported scenario:
        Resume: Python, Pandas, NumPy, Scikit-Learn, TensorFlow, SQL
        Job requires: Statistical Analysis, Scientific Analysis, Database Management, Coding

        Previous result: 0%. Expected: high match via taxonomy.
        """
        profile = StructuredResumeProfile(
            technical_skills=["Python", "Pandas", "NumPy", "Scikit-Learn", "TensorFlow", "SQL"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Statistical Analysis", "Scientific Analysis", "Database Management", "Coding"]

        result = ATSService.calculate_match(profile, required)

        # All four should be at least partially matched via taxonomy
        total_matched = len(result.matched_keywords) + len(result.partially_matched_keywords)
        self.assertEqual(total_matched, 4, f"Expected 4 matches, got {total_matched}. Missing: {result.missing_keywords}")
        self.assertEqual(len(result.missing_keywords), 0)
        self.assertGreaterEqual(result.ats_score, 75)

    def test_mixed_direct_and_partial(self) -> None:
        """Mix of direct matches and synonym matches produces correct weighted score."""
        profile = StructuredResumeProfile(
            technical_skills=["Python", "SQL", "Pandas"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        # Use a truly unknown skill to test missing
        required = ["Python", "SQL", "Data Analysis", "GNSS"]

        result = ATSService.calculate_match(profile, required)

        # Python: direct, SQL: direct, Data Analysis: partial via Pandas, GNSS: missing
        self.assertEqual(len(result.matched_keywords), 2)  # Python, SQL
        self.assertEqual(len(result.partially_matched_keywords), 1)  # Data Analysis
        self.assertEqual(len(result.missing_keywords), 1)  # GNSS
        # Score: (2 + 0.8*1) / 4 * 100 = 70%
        self.assertEqual(result.ats_score, 70)

    def test_direct_match_takes_precedence(self) -> None:
        """If a skill matches directly, it should not also appear as partial."""
        profile = StructuredResumeProfile(
            technical_skills=["Python", "Machine Learning"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Machine Learning"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.matched_keywords), 1)
        self.assertEqual(result.matched_keywords[0], "Machine Learning")
        self.assertEqual(len(result.partially_matched_keywords), 0)
        self.assertEqual(result.ats_score, 100)

    def test_no_match_unknown_skills(self) -> None:
        """Skills not in taxonomy and not in resume text should be missing."""
        profile = StructuredResumeProfile(
            technical_skills=["Python"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["GNSS", "WGS84", "MATLAB"]

        result = ATSService.calculate_match(profile, required)

        self.assertEqual(len(result.missing_keywords), 3)
        self.assertEqual(result.ats_score, 0)


class TestATSStructuredProfile(unittest.TestCase):
    """Test ATS scoring with full structured resume profiles."""

    def test_experience_text_matches(self) -> None:
        """Skills mentioned in experience summaries should be matchable."""
        profile = StructuredResumeProfile(
            technical_skills=[],
            experience=[
                ExperienceItem(
                    title="Data Analyst",
                    company="Test Corp",
                    summary="Performed statistical analysis using Python and SQL for business intelligence.",
                )
            ],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Statistical Analysis", "Python"]

        result = ATSService.calculate_match(profile, required)

        # Both should be direct matches since the text contains the exact phrases
        self.assertEqual(len(result.matched_keywords), 2)
        self.assertEqual(result.ats_score, 100)

    def test_project_technologies_used_for_matching(self) -> None:
        """Technologies listed in projects should participate in taxonomy matching."""
        profile = StructuredResumeProfile(
            technical_skills=[],
            experience=[],
            projects=[
                ProjectItem(
                    name="ML Pipeline",
                    technologies=["Python", "TensorFlow", "Pandas"],
                    summary="Built a machine learning pipeline.",
                )
            ],
            education=[],
            achievements=[],
            certifications=[],
        )
        required = ["Machine Learning", "Data Analysis"]

        result = ATSService.calculate_match(profile, required)

        # "machine learning" is in project summary text → direct match
        # "Data Analysis" → partial via pandas
        total = len(result.matched_keywords) + len(result.partially_matched_keywords)
        self.assertGreaterEqual(total, 2)
        self.assertEqual(len(result.missing_keywords), 0)


class TestATSRecommendations(unittest.TestCase):
    """Verify recommendation generation for different match tiers."""

    def test_missing_skills_recommendations(self) -> None:
        """Missing skills should produce incorporation recommendations."""
        result = ATSService.calculate_match("Python developer.", ["GNSS", "MATLAB"])

        self.assertTrue(any("GNSS" in r for r in result.recommendations))

    def test_partial_match_recommendations(self) -> None:
        """Partial matches should produce strengthening recommendations."""
        profile = StructuredResumeProfile(
            technical_skills=["Pandas", "NumPy"],
            experience=[],
            projects=[],
            education=[],
            achievements=[],
            certifications=[],
        )
        result = ATSService.calculate_match(profile, ["Statistical Analysis"])

        self.assertTrue(
            any("Strengthen" in r or "explicitly" in r for r in result.recommendations)
        )

    def test_perfect_match_recommendations(self) -> None:
        """Perfect matches should produce positive feedback."""
        result = ATSService.calculate_match("Python SQL Docker", ["Python", "SQL", "Docker"])

        self.assertTrue(
            any("Excellent" in r for r in result.recommendations)
        )


if __name__ == "__main__":
    unittest.main()
