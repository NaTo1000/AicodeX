"""Standard-library tests for the AicodeX Edition 2 metrics panel."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.metrics import MetricsPanel, UsageRecord

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
COSTS = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["metrics"]["cost_per_token_usd"]


def _panel() -> MetricsPanel:
    return MetricsPanel(cost_per_token=COSTS)


class UsageRecordTests(unittest.TestCase):
    def test_cost_derived_from_config(self) -> None:
        panel = _panel()
        record = panel.record_output("Claude", tokens=1000)
        self.assertAlmostEqual(record.cost_usd, COSTS["Claude"] * 1000, places=6)

    def test_explicit_cost_overrides_config(self) -> None:
        panel = _panel()
        record = panel.record_output("Claude", tokens=1000, cost_usd=0.5)
        self.assertEqual(record.cost_usd, 0.5)

    def test_negative_tokens_rejected(self) -> None:
        panel = _panel()
        with self.assertRaises(ValueError):
            panel.record(UsageRecord(model="Claude", tokens=-1))


class AggregationTests(unittest.TestCase):
    def test_per_model_aggregation(self) -> None:
        panel = _panel()
        panel.record_output("Claude", tokens=1000, user="alice")
        panel.record_output("Claude", tokens=500, user="bob")
        panel.record_output("Mistral", tokens=2000, user="alice")
        stats = panel.per_model()
        self.assertEqual(stats["Claude"].outputs, 2)
        self.assertEqual(stats["Claude"].tokens, 1500)
        self.assertEqual(stats["Claude"].users, {"alice", "bob"})
        self.assertEqual(stats["Mistral"].tokens, 2000)

    def test_cost_per_token(self) -> None:
        panel = _panel()
        panel.record_output("Claude", tokens=1000)
        stats = panel.per_model()["Claude"]
        self.assertAlmostEqual(stats.cost_per_token, COSTS["Claude"], places=8)

    def test_platform_totals_across_users(self) -> None:
        panel = _panel()
        panel.record_output("Claude", tokens=1000, user="alice")
        panel.record_output("Mistral", tokens=2000, user="bob")
        panel.record_output("Grok", tokens=500, user="carol")
        total = panel.totals()
        self.assertEqual(total.outputs, 3)
        self.assertEqual(total.tokens, 3500)
        self.assertEqual(total.users, {"alice", "bob", "carol"})

    def test_empty_panel_totals_zero(self) -> None:
        total = _panel().totals()
        self.assertEqual(total.outputs, 0)
        self.assertEqual(total.tokens, 0)
        self.assertEqual(total.cost_per_token, 0.0)


class SwapSuggestionTests(unittest.TestCase):
    def test_suggests_cheaper_equal_value_model(self) -> None:
        # Use explicit costs so the value relationship is unambiguous.
        panel = MetricsPanel()
        # Expensive, low value.
        panel.record_output("Expensive", tokens=100, cost_usd=1.0)
        # Cheaper per token, >= tokens/output (equal-or-more value).
        panel.record_output("Cheap", tokens=200, cost_usd=0.1)
        suggestions = panel.swap_suggestions()
        self.assertTrue(any("Expensive -> Cheap" in s for s in suggestions))

    def test_no_suggestion_when_cheaper_is_lower_value(self) -> None:
        panel = MetricsPanel()
        panel.record_output("Expensive", tokens=500, cost_usd=1.0)
        panel.record_output("Cheap", tokens=100, cost_usd=0.1)
        suggestions = panel.swap_suggestions()
        self.assertFalse(any("Expensive -> Cheap" in s for s in suggestions))

    def test_no_suggestions_on_empty(self) -> None:
        self.assertEqual(_panel().swap_suggestions(), [])


class RenderTests(unittest.TestCase):
    def test_render_text(self) -> None:
        panel = _panel()
        panel.record_output("Claude", tokens=1000, user="alice")
        text = panel.render_text()
        self.assertIn("Metrics Control Deck", text)
        self.assertIn("Claude", text)
        self.assertIn("TOTAL", text)

    def test_render_page_is_html_and_escaped(self) -> None:
        panel = _panel()
        panel.record_output("Claude", tokens=1000, user="alice")
        page = panel.render_page()
        self.assertIn("<html", page)
        self.assertIn("Model Value Metrics", page)
        self.assertIn("Claude", page)
        self.assertIn("TOTAL", page)

    def test_render_page_escapes_model_names(self) -> None:
        panel = MetricsPanel()
        panel.record_output("<script>alert(1)</script>", tokens=10, cost_usd=0.1)
        page = panel.render_page()
        self.assertNotIn("<script>", page)
        self.assertIn("&lt;script&gt;", page)


class CliTests(unittest.TestCase):
    def test_metrics_flag(self) -> None:
        self.assertEqual(cli_main(["--metrics", "--config", str(CONFIG_PATH)]), 0)

    def test_metrics_html_writes_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "metrics.html"
            rc = cli_main(["--metrics-html", str(out),
                           "--config", str(CONFIG_PATH)])
            self.assertEqual(rc, 0)
            self.assertTrue(out.exists())
            self.assertIn("Model Value Metrics", out.read_text())


if __name__ == "__main__":
    unittest.main()
