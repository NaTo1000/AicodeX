"""Standard-library tests for the AicodeX Edition 2 crossover database."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from edition2.__main__ import main as cli_main
from edition2.crossover import CrossoverDatabase, CrossoverEntry
from edition2.orchestrator import ConfigError

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"
ENTRIES = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))["crossover"]["entries"]


class EntryValidationTests(unittest.TestCase):
    def test_valid_entry_builds(self) -> None:
        db = CrossoverDatabase(ENTRIES)
        self.assertEqual(len(db.all()), 4)

    def test_missing_field_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            CrossoverDatabase({"bad": {"source_lang": "python"}})

    def test_non_object_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            CrossoverDatabase({"bad": ["not", "an", "object"]})


class LookupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db = CrossoverDatabase(ENTRIES)

    def test_exact_lookup(self) -> None:
        entry = self.db.lookup("python", "swift", "list comprehension")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.emulation, "items.filter { $0 > 0 }.map { $0 * 2 }")

    def test_lookup_missing_returns_none(self) -> None:
        self.assertIsNone(self.db.lookup("python", "swift", "nonexistent"))

    def test_emulate_returns_text(self) -> None:
        text = self.db.emulate("python", "rust", "f-string interpolation")
        self.assertEqual(text, 'format!("value={value}")')

    def test_find_by_language(self) -> None:
        from_python = self.db.find(source_lang="python")
        self.assertEqual(len(from_python), 3)
        to_swift = self.db.find(target_lang="swift")
        self.assertEqual(len(to_swift), 2)

    def test_languages_listed(self) -> None:
        langs = self.db.languages()
        for lang in ("python", "swift", "javascript", "rust"):
            self.assertIn(lang, langs)


class RenderTests(unittest.TestCase):
    def test_render(self) -> None:
        text = CrossoverDatabase(ENTRIES).render()
        self.assertIn("Crossover & Emulation Database", text)
        self.assertIn("entries: 4", text)
        self.assertIn("python -> swift", text)

    def test_add_entry(self) -> None:
        db = CrossoverDatabase()
        db.add(CrossoverEntry(source_lang="c", target_lang="rust",
                              construct="pointer", source="int* p",
                              emulation="let p: *mut i32"))
        self.assertEqual(len(db.all()), 1)


class CliTests(unittest.TestCase):
    def test_crossover_flag(self) -> None:
        self.assertEqual(cli_main(["--crossover", "--config", str(CONFIG_PATH)]), 0)


if __name__ == "__main__":
    unittest.main()
