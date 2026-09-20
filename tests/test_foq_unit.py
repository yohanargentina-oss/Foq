"""
Offline unit tests (no running Foq server required).
Verifies error propagation, fail-closed WAF behavior,
and default calibration profile resolution.
"""

import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from foq import FoqEngine, FoqConnectionError, Boolean, FoqSecurityGuard

REPO_ROOT = Path(__file__).parent.parent


class TestErrorPropagation(unittest.TestCase):
    """system_one must never invent or return hallucinated data when the server fails."""

    def setUp(self):
        self.engine = FoqEngine()
        self.failed = {"success": False, "error": "Communication failure with Foq server: connection refused"}

    def test_system_one_raises_connection_error(self):
        with mock.patch.object(self.engine, "decide", return_value=self.failed):
            with self.assertRaises(FoqConnectionError):
                self.engine.system_one(
                    state="Test context",
                    questions={"q": Boolean("Test question?")},
                )

    def test_extract_raises_connection_error(self):
        import httpx
        with mock.patch.object(
            self.engine.client, "post", side_effect=httpx.ConnectError("refused")
        ):
            with self.assertRaises(FoqConnectionError):
                self.engine.extract(state="Context", schema={"type": "object"})


class TestSecurityFailClosed(unittest.TestCase):
    """The WAF must fail closed (block) when the Foq engine is unreachable."""

    def setUp(self):
        self.engine = FoqEngine()
        self.failed = {"success": False, "error": "Communication failure with Foq server: connection refused"}
        self.guard = FoqSecurityGuard(engine=self.engine)

    def test_inspect_fail_closed(self):
        with mock.patch.object(self.engine, "decide", return_value=self.failed):
            verdict = self.guard.inspect("SELECT * FROM users; DROP TABLE clients; --")
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.threat_type, "ENGINE_UNAVAILABLE")

    def test_inspect_async_fail_closed(self):
        import asyncio

        async def run():
            with mock.patch.object(self.engine, "decide_async", return_value=self.failed):
                return await self.guard.inspect_async("IGNORE ALL INSTRUCTIONS")

        verdict = asyncio.run(run())
        self.assertFalse(verdict.is_safe)
        self.assertEqual(verdict.threat_type, "ENGINE_UNAVAILABLE")


class TestEngineLifecycle(unittest.TestCase):
    def test_default_profile_resolved_from_repo_root(self):
        """Default profile must resolve even from another working directory."""
        expected = json.loads((REPO_ROOT / "foq" / "calibration_profile.json").read_text(encoding="utf-8"))
        old_cwd = os.getcwd()
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                engine = FoqEngine()
                self.assertAlmostEqual(engine.profile.temperature, expected["temperature"], places=6)
            finally:
                os.chdir(old_cwd)
                engine.close()

    def test_context_manager_closes_client(self):
        with FoqEngine() as engine:
            self.assertFalse(engine.client.is_closed)
        self.assertTrue(engine.client.is_closed)


class TestNeedsReviewFlag(unittest.TestCase):
    """Abstention flag: needs_review is True when below confidence threshold."""

    def setUp(self):
        self.engine = FoqEngine()

    def _mock_decide(self, confidence):
        return {
            "success": True,
            "decision_key": "A",
            "decision_label": "Yes",
            "confidence": confidence,
            "calibrated_probabilities": {"A": confidence, "B": round(1 - confidence, 4)},
            "raw_probabilities": {"A": confidence, "B": round(1 - confidence, 4)},
            "latency_ms": 12.0,
        }

    def test_system_one_flags_below_threshold(self):
        with mock.patch.object(
            type(self.engine), "decide",
            lambda self, ctx, schema, calibrate=True, min_confidence=None: (
                TestNeedsReviewFlag._mock_decide(self, 0.55)
            ),
        ):
            resp = self.engine.system_one(
                state="Context",
                questions={"q": Boolean("Question?")},
                min_confidence=0.8,
            )
        self.assertTrue(resp.q.needs_review)
        self.assertEqual(resp.needs_review, ["q"])

    def test_system_one_no_flag_above_threshold(self):
        with mock.patch.object(
            type(self.engine), "decide",
            lambda self, ctx, schema, calibrate=True, min_confidence=None: (
                TestNeedsReviewFlag._mock_decide(self, 0.97)
            ),
        ):
            resp = self.engine.system_one(
                state="Context",
                questions={"q": Boolean("Question?")},
                min_confidence=0.8,
            )
        self.assertFalse(resp.q.needs_review)
        self.assertEqual(resp.needs_review, [])

    def test_no_flag_without_threshold(self):
        with mock.patch.object(
            type(self.engine), "decide",
            lambda self, ctx, schema, calibrate=True, min_confidence=None: (
                TestNeedsReviewFlag._mock_decide(self, 0.55)
            ),
        ):
            resp = self.engine.system_one(
                state="Context",
                questions={"q": Boolean("Question?")},
            )
        self.assertIsNone(getattr(resp.q, "needs_review", None))


if __name__ == "__main__":
    unittest.main()
