import unittest
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "backend-python"))

import analyzer  # noqa: E402


class AnalyzerTests(unittest.TestCase):
    def test_detects_matching_skills_from_job_description(self):
        result = analyzer.analyze(
            {
                "resumeText": """
                Email: student@example.com
                GitHub: https://github.com/student
                LinkedIn: https://linkedin.com/in/student
                Education B.Tech Computer Engineering
                Skills Java, Python, Spring Boot, FastAPI, React, SQL, PostgreSQL, Docker, Git, DSA, OOP
                Projects Built a resume analyzer using Java APIs and a Python analysis engine.
                Experience Implemented and deployed REST APIs.
                """,
                "jobDescription": "Java Spring Boot Python FastAPI React SQL PostgreSQL Docker Git DSA OOP",
            }
        )

        self.assertTrue(result["ok"])
        self.assertGreaterEqual(result["score"], 70)
        self.assertIn("Java", result["matchedSkills"])
        self.assertIn("Python", result["matchedSkills"])

    def test_reports_missing_skills(self):
        result = analyzer.analyze(
            {
                "resumeText": "Education B.Tech Skills Python Projects Built scripts using Python.",
                "targetRole": "Backend Developer",
            }
        )

        self.assertTrue(result["ok"])
        self.assertIn("Spring Boot", result["missingSkills"])
        self.assertIn("REST APIs", result["missingSkills"])

    def test_requires_resume_text(self):
        result = analyzer.analyze({"resumeText": ""})

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "Resume text is required.")


if __name__ == "__main__":
    unittest.main()
