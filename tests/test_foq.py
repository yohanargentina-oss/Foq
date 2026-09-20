"""
Unit tests for Foq decision primitives (Boolean, Choice, Score, SecurityGuard).
"""

import unittest
from foq import (
    FoqEngine,
    Boolean,
    Bool,
    BooleanResult,
    BoolResult,
    Noul,
    Choice,
    Score,
    Structure,
    FoqSecurityGuard,
    SecurityVerdict,
    TemperatureScaler,
    CalibrationProfile,
)


class TestFoqPrimitives(unittest.TestCase):
    def test_boolean_primitive(self):
        b = Boolean("Is this transaction fraudulent?")
        self.assertEqual(b.name, "boolean")
        self.assertEqual(b.get_keys(), ["A", "B"])

        prompt = b.format_prompt("User transaction: $5,000 to unknown account.")
        self.assertIn("Tu es Foq", prompt)
        self.assertIn("<donnees>", prompt)
        self.assertIn("User transaction: $5,000", prompt)

        # Test aliases
        self.assertIs(Bool, Boolean)
        self.assertIs(Noul, Boolean)
        self.assertIs(BoolResult, BooleanResult)

        # Test parsing
        res = b.parse_result({
            "decision_key": "A",
            "calibrated_probabilities": {"A": 0.95, "B": 0.05},
            "latency_ms": 42.0,
        })
        self.assertIsInstance(res, BooleanResult)
        self.assertTrue(res.answer)
        self.assertEqual(res.confidence, 0.95)
        self.assertEqual(res.latency_ms, 42.0)

    def test_choice_primitive(self):
        c = Choice(
            "Which department should handle this?",
            choices={"billing": "Billing", "tech": "Technical support"}
        )
        self.assertEqual(c.name, "choice")
        self.assertEqual(c.get_keys(), ["A", "B"])

        res = c.parse_result({
            "decision_key": "A",
            "decision_label": "Billing",
            "confidence": 0.88,
            "calibrated_probabilities": {"A": 0.88, "B": 0.12},
            "latency_ms": 50.0,
        })
        self.assertEqual(res.choice, "billing")
        self.assertEqual(res.confidence, 0.88)

    def test_score_primitive(self):
        s = Score(
            "Rate severity",
            levels={"1": "Low", "2": "Medium", "3": "Critical"}
        )
        self.assertEqual(s.name, "score")
        res = s.parse_result({
            "decision_key": "C",
            "confidence": 0.70,
            "calibrated_probabilities": {"A": 0.1, "B": 0.2, "C": 0.7},
            "latency_ms": 30.0,
        })
        self.assertEqual(res.level, "3")
        self.assertAlmostEqual(res.score, 2.6, places=1)

    def test_security_guard_init(self):
        guard = FoqSecurityGuard()
        self.assertIsNotNone(guard.engine)
        self.assertEqual(guard._schema.name, "security_audit")

    def test_calibration_profile(self):
        profile = CalibrationProfile()
        loaded = profile.load()
        self.assertTrue(loaded)
        self.assertEqual(profile.model_alias, "foq")
        self.assertGreater(profile.temperature, 0.0)


if __name__ == "__main__":
    unittest.main()
