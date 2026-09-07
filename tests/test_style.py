"""Standard-library tests for the AicodeX Edition 2 style database."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.style import StyleDatabase, StyleFingerprint

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
DEFAULT_FP = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["style"]["default_fingerprint"]

TAB_SAMPLE = 'def f():\n\treturn "x"\n'
SPACE_SAMPLE = 'def f():\n    return "x"\n'
SINGLE_QUOTE_SAMPLE = "def f():\n    return 'x'\n"


class FingerprintInferenceTests(unittest.TestCase):
    def test_detects_space_indent(self) -> None:
        fp = StyleDatabase().learn([SPACE_SAMPLE])
        self.assertFalse(fp.use_tabs)
        self.assertEqual(fp.indent_width, 4)

    def test_detects_tab_indent(self) -> None:
        fp = StyleDatabase().learn([TAB_SAMPLE])
        self.assertTrue(fp.use_tabs)

    def test_detects_quote_preference(self) -> None:
        self.assertEqual(StyleDatabase().learn([SINGLE_QUOTE_SAMPLE]).quote, "'")
        self.assertEqual(StyleDatabase().learn([SPACE_SAMPLE]).quote, '"')

    def test_detects_trailing_newline(self) -> None:
        self.assertTrue(StyleDatabase().learn([SPACE_SAMPLE]).trailing_newline)
        self.assertFalse(StyleDatabase().learn(["def f():\n    pass"]).trailing_newline)

    def test_learn_increments_rereads(self) -> None:
        db = StyleDatabase()
        db.learn([SPACE_SAMPLE])
        db.learn([SPACE_SAMPLE])
        self.assertEqual(db.rereads, 2)


class AlignmentTests(unittest.TestCase):
    def test_no_drift_when_aligned(self) -> None:
        db = StyleDatabase()
        db.learn([SPACE_SAMPLE])
        self.assertEqual(db.alignment_drift([SPACE_SAMPLE]), {})

    def test_drift_detected_on_style_change(self) -> None:
        db = StyleDatabase()
        db.learn([SPACE_SAMPLE])
        drift = db.alignment_drift([SINGLE_QUOTE_SAMPLE])
        self.assertIn("quote", drift)

    def test_align_updates_fingerprint(self) -> None:
        db = StyleDatabase()
        db.learn([SPACE_SAMPLE])
        db.align([SINGLE_QUOTE_SAMPLE])
        self.assertEqual(db.fingerprint.quote, "'")


class RestyleTests(unittest.TestCase):
    def test_restyle_converts_to_tabs(self) -> None:
        db = StyleDatabase(StyleFingerprint(use_tabs=True))
        out = db.restyle(SPACE_SAMPLE)
        self.assertIn("\treturn", out)

    def test_restyle_converts_to_single_quotes(self) -> None:
        db = StyleDatabase(StyleFingerprint(quote="'"))
        out = db.restyle('x = "hello"\n')
        self.assertIn("'hello'", out)

    def test_restyle_preserves_content(self) -> None:
        db = StyleDatabase()
        out = db.restyle(SPACE_SAMPLE)
        self.assertIn("return", out)
        self.assertIn("def f():", out)

    def test_restyle_trailing_newline(self) -> None:
        db = StyleDatabase(StyleFingerprint(trailing_newline=True))
        self.assertTrue(db.restyle("x = 1").endswith("\n"))
        db2 = StyleDatabase(StyleFingerprint(trailing_newline=False))
        self.assertFalse(db2.restyle("x = 1").endswith("\n"))

    def test_default_config_fingerprint(self) -> None:
        self.assertEqual(DEFAULT_FP["indent_width"], 4)
        self.assertEqual(DEFAULT_FP["quote"], '"')


class CliTests(unittest.TestCase):
    def test_style_fingerprint_flag(self) -> None:
        self.assertEqual(
            cli_main(["--style-fingerprint", SPACE_SAMPLE,
                      "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()
