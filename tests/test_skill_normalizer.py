"""
Skill Normalizer Tests
========================
Tests for services/skill_normalizer.py.

Verifies:
- Preamble stripping
- Technology extraction from sentences
- Phrase-to-skill mapping
- Clean passthrough for already-normalized labels
- Full pipeline normalization
- The exact user-reported scenario
"""

from __future__ import annotations

import unittest
from services.skill_normalizer import normalize_skill, normalize_skills


class TestNormalizeSkillPassthrough(unittest.TestCase):
    """Short, clean skill labels should pass through unchanged."""

    def test_single_word_passthrough(self) -> None:
        result = normalize_skill("Python")
        self.assertEqual(result, ["Python"])

    def test_two_word_passthrough(self) -> None:
        result = normalize_skill("Machine Learning")
        self.assertEqual(result, ["Machine Learning"])

    def test_short_technology_passthrough(self) -> None:
        result = normalize_skill("SQL")
        self.assertEqual(result, ["SQL"])

    def test_empty_string(self) -> None:
        result = normalize_skill("")
        self.assertEqual(result, [])

    def test_whitespace_only(self) -> None:
        result = normalize_skill("   ")
        self.assertEqual(result, [])


class TestNormalizePreambleStripping(unittest.TestCase):
    """Verbose requirement sentences should be decomposed into skill labels."""

    def test_experience_with_technologies(self) -> None:
        """The exact user-reported failure case."""
        result = normalize_skill(
            "Experience with coding or algorithm development, including Fortran, C/C++, IDL, R, Python, SQL, Visual Basic, or UNIX scripting"
        )
        result_lower = [r.lower() for r in result]
        self.assertIn("programming", result_lower)
        self.assertIn("python", result_lower)
        self.assertIn("sql", result_lower)

    def test_experience_using_scientific_modeling(self) -> None:
        result = normalize_skill(
            "Experience using scientific modeling systems for statistical or predictive analysis"
        )
        result_lower = [r.lower() for r in result]
        self.assertTrue(
            "statistical analysis" in result_lower or "scientific modeling" in result_lower,
            f"Expected 'Statistical Analysis' or 'Scientific Modeling' in {result}"
        )

    def test_experience_working_collaboratively(self) -> None:
        result = normalize_skill(
            "Experience working collaboratively as part of a team"
        )
        result_lower = [r.lower() for r in result]
        self.assertIn("team collaboration", result_lower)

    def test_ability_to_prefix(self) -> None:
        result = normalize_skill("Ability to perform data analysis")
        result_lower = [r.lower() for r in result]
        self.assertIn("data analysis", result_lower)

    def test_knowledge_of_prefix(self) -> None:
        result = normalize_skill("Knowledge of machine learning techniques")
        result_lower = [r.lower() for r in result]
        self.assertIn("machine learning", result_lower)

    def test_quantitative_data(self) -> None:
        result = normalize_skill(
            "Experience with analyzing and interpreting quantitative data"
        )
        result_lower = [r.lower() for r in result]
        self.assertIn("quantitative analysis", result_lower)


class TestNormalizeTechnologyExtraction(unittest.TestCase):
    """Known technologies should be extracted from verbose text."""

    def test_extract_python_sql(self) -> None:
        result = normalize_skill(
            "Proficiency in Python and SQL for data processing"
        )
        result_lower = [r.lower() for r in result]
        self.assertIn("python", result_lower)
        self.assertIn("sql", result_lower)

    def test_extract_from_including_list(self) -> None:
        result = normalize_skill(
            "Programming experience including Python, Java, and Docker"
        )
        result_lower = [r.lower() for r in result]
        self.assertIn("python", result_lower)
        self.assertIn("java", result_lower)
        self.assertIn("docker", result_lower)


class TestNormalizeSkillsList(unittest.TestCase):
    """Test the full pipeline with a list of raw skills."""

    def test_mixed_clean_and_verbose(self) -> None:
        """Mix of clean labels and verbose sentences."""
        raw = [
            "Python",
            "Experience with SQL and database management",
            "Team Collaboration",
        ]
        result = normalize_skills(raw)
        result_lower = [r.lower() for r in result]
        self.assertIn("python", result_lower)
        self.assertIn("sql", result_lower)
        self.assertIn("team collaboration", result_lower)

    def test_deduplication(self) -> None:
        """Duplicate skills from different sources should be merged."""
        raw = ["Python", "Experience with Python programming"]
        result = normalize_skills(raw)
        python_count = sum(1 for r in result if r.lower() == "python")
        self.assertEqual(python_count, 1)

    def test_user_scenario_full(self) -> None:
        """
        Full user-reported scenario:
        Three verbose requirement sentences → normalized to concise labels.
        """
        raw = [
            "Experience with analyzing and interpreting quantitative data",
            "Experience with coding or algorithm development, including Fortran, C/C++, IDL, R, Python, SQL, Visual Basic, or UNIX scripting",
            "Experience using scientific modeling systems for statistical or predictive analysis",
        ]
        result = normalize_skills(raw)
        result_lower = [r.lower() for r in result]

        # Must extract specific technologies
        self.assertIn("python", result_lower)
        self.assertIn("sql", result_lower)

        # Must extract abstract competencies
        self.assertTrue(
            "quantitative analysis" in result_lower or "data analysis" in result_lower,
            f"Expected quantitative/data analysis in {result}"
        )
        self.assertTrue(
            "statistical analysis" in result_lower or "scientific modeling" in result_lower,
            f"Expected statistical analysis or scientific modeling in {result}"
        )

        # Must NOT contain full sentences
        for skill in result:
            self.assertLess(
                len(skill), 40,
                f"Skill label too long (still a sentence?): '{skill}'"
            )


if __name__ == "__main__":
    unittest.main()
