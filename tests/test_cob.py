"""Standard-library tests for the AicodeX Edition 2 COB daily report."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.cob import CobReporter, ImprovementRequest

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
COB_CFG = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["monitor"]["cob"]


class BestPerJobTests(unittest.TestCase):
    def test_best_per_job_picks_highest_score(self) -> None:
        reporter = CobReporter(jobs=COB_CFG["jobs"])
        reporter.record_score("Claude", "structure", 88.0)
        reporter.record_score("Gemini", "structure", 91.5)
        reporter.record_score("Cursor", "implementation", 76.0)
        best = reporter.best_per_job()
        self.assertEqual(best["structure"].component, "Gemini")
        self.assertEqual(best["implementation"].component, "Cursor")

    def test_best_per_job_empty(self) -> None:
        self.assertEqual(CobReporter().best_per_job(), {})

    def test_tie_keeps_first(self) -> None:
        reporter = CobReporter()
        reporter.record_score("A", "research", 50.0)
        reporter.record_score("B", "research", 50.0)
        self.assertEqual(reporter.best_per_job()["research"].component, "A")


class ImprovementTests(unittest.TestCase):
    def test_channels(self) -> None:
        reporter = CobReporter()
        reporter.add_improvement("Dark mode", "alice", channel="email",
                                 contact="alice@example.com")
        reporter.add_improvement("Faster sync", "bob", channel="voice",
                                 contact="thread-42")
        reporter.add_improvement("More docs", "carol")
        report = reporter.build(day="2026-09-04")
        channels = {r.channel for r in report.improvements}
        self.assertEqual(channels, {"email", "voice", "forum"})

    def test_invalid_channel_rejected(self) -> None:
        with self.assertRaises(ValueError):
            CobReporter().add_improvement("x", "y", channel="sms")

    def test_channel_label(self) -> None:
        self.assertEqual(
            ImprovementRequest("t", "u", channel="voice").channel_label(),
            "voice message")
        self.assertEqual(
            ImprovementRequest("t", "u", channel="email").channel_label(), "email")


class ReportRenderTests(unittest.TestCase):
    def test_report_text(self) -> None:
        reporter = CobReporter()
        reporter.record_score("Mistral", "research", 95.0)
        reporter.add_improvement("Better caching", "dana", channel="email",
                                 contact="dana@example.com")
        text = reporter.build(day="2026-09-04").render_text()
        self.assertIn("AicodeX Daily Build Report — 2026-09-04", text)
        self.assertIn("Mistral", text)
        self.assertIn("Better caching", text)
        self.assertIn("email", text)

    def test_daily_article(self) -> None:
        reporter = CobReporter()
        reporter.record_score("Grok", "security", 97.0)
        article = reporter.daily_article(day="2026-09-04")
        self.assertIn("# AicodeX Daily Build Report — 2026-09-04", article)
        self.assertIn("**security** — Grok", article)

    def test_build_defaults_to_today(self) -> None:
        report = CobReporter().build()
        self.assertRegex(report.day, r"^\d{4}-\d{2}-\d{2}$")


class CliTests(unittest.TestCase):
    def test_cob_report_flag(self) -> None:
        self.assertEqual(cli_main(["--cob-report", "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()
