"""
Tests for the languages catalog, the HiAi + PECs code predictor, and the
additional AI model provider adapters.
"""

import json
import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from assistant import AssistantEngine
from interaction import (
    CodePredictor,
    InteractionController,
    LanguageCatalog,
)
from interaction.languages import FORMATS
from interaction.providers import (
    ADAPTER_KINDS,
    GeminiProvider,
    Grok4Provider,
    OpenRouterProvider,
    ProviderManager,
    ProviderRegistry,
)


class LanguageCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = LanguageCatalog()

    def test_has_world_languages(self):
        for name in ("python", "javascript", "typescript", "swift", "rust", "go",
                     "java", "c", "cpp", "csharp", "ruby", "php", "sql", "html"):
            self.assertIsNotNone(self.catalog.get(name), name)

    def test_variants_and_formats(self):
        swift = self.catalog.get("swift")
        self.assertIn("swiftui", swift.variants)
        self.assertIn("source", swift.formats)

    def test_by_extension(self):
        self.assertEqual(self.catalog.by_extension("py").name, "python")
        self.assertEqual(self.catalog.by_extension(".rs").name, "rust")
        self.assertIsNone(self.catalog.by_extension("nope"))

    def test_formats_catalog(self):
        for fmt in ("json", "yaml", "xml", "csv", "markdown", "html", "sql"):
            self.assertIn(fmt, FORMATS)


class CodePredictorTests(unittest.TestCase):
    def setUp(self):
        self.predictor = CodePredictor()

    def test_python_detection(self):
        code = "def quicksort(arr):\n    if len(arr) <= 1:\n        return arr\n    return sorted(arr)\n"
        pred = self.predictor.predict(code, filename="s.py")
        self.assertEqual(pred.language, "python")
        self.assertEqual(pred.variant, "cpython")
        self.assertGreater(pred.language_confidence, 0.0)
        self.assertEqual(pred.algorithm, "sorting")

    def test_swiftui_detection(self):
        code = ("import SwiftUI\nstruct V: View {\n  @State var n = 0\n"
                "  var body: some View { Text(\"hi\") }\n}\n")
        pred = self.predictor.predict(code, filename="V.swift")
        self.assertEqual(pred.language, "swift")
        self.assertEqual(pred.variant, "swiftui")

    def test_sql_detection(self):
        pred = self.predictor.predict("SELECT name FROM users WHERE id = 1;", filename="q.sql")
        self.assertEqual(pred.language, "sql")
        self.assertEqual(pred.format, "sql")

    def test_json_format_detection(self):
        code = "import json\ndata = json.loads(payload)\nprint(json.dumps(data))"
        pred = self.predictor.predict(code, filename="p.py")
        self.assertEqual(pred.format, "json")

    def test_csv_format_detection(self):
        code = "import csv\nrows = list(csv.reader(src))"
        pred = self.predictor.predict(code, filename="c.py")
        self.assertEqual(pred.format, "csv")

    def test_algorithm_detection_concurrency(self):
        code = "async function f(){ await run(); }\n"
        pred = self.predictor.predict(code, filename="a.js")
        self.assertEqual(pred.algorithm, "concurrency")

    def test_empty_submission(self):
        pred = self.predictor.predict("   ")
        self.assertEqual(pred.language, "unknown")
        self.assertEqual(pred.language_confidence, 0.0)
        self.assertIn("Empty", pred.rationale)

    def test_extension_hint_boosts_language(self):
        # Ambiguous short snippet; extension resolves it.
        pred = self.predictor.predict("print(1)", filename="script.py")
        self.assertEqual(pred.language, "python")

    def test_candidates_ranked(self):
        pred = self.predictor.predict("def f():\n    pass\n", filename="x.py")
        self.assertTrue(pred.candidates)
        self.assertEqual(pred.candidates[0][0], "python")

    def test_prediction_includes_terms(self):
        pred = self.predictor.predict("def analyze(data): return sorted(data)", filename="a.py")
        self.assertTrue(pred.terms)


class NewProviderAdapterTests(unittest.TestCase):
    def test_new_kinds_registered(self):
        for kind in ("grok4", "openrouter", "gemini", "chatgptcodex",
                     "chatgpt6luna", "claudecoder", "codex", "minstrel",
                     "kodex", "xcode", "generic"):
            self.assertIn(kind, ADAPTER_KINDS)

    def test_grok4_openai_style_request(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = json.loads(payload.decode())
            return {"choices": [{"message": {"content": "grok says hi"}}]}

        p = Grok4Provider(
            name="grok4", endpoint="https://api.x.ai/v1",
            api_key_env="XAI_API_KEY", transport=transport,
            environ={"XAI_API_KEY": "k"},
        )
        resp = p.generate("grok-4-latest", "hello")
        self.assertEqual(resp.text, "grok says hi")
        self.assertEqual(captured["url"], "https://api.x.ai/v1/chat/completions")
        self.assertEqual(captured["payload"]["model"], "grok-4-latest")
        self.assertIn("Authorization", captured["headers"])

    def test_gemini_uses_query_param_key(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured["url"] = url
            captured["payload"] = json.loads(payload.decode())
            return {"candidates": [{"content": {"parts": [{"text": "gemini ok"}]}}]}

        p = GeminiProvider(
            name="gemini", endpoint="https://generativelanguage.googleapis.com/v1beta",
            api_key_env="GEMINI_API_KEY", transport=transport,
            environ={"GEMINI_API_KEY": "gk"},
        )
        resp = p.generate("gemini-2.0-flash", "hello")
        self.assertEqual(resp.text, "gemini ok")
        self.assertIn("generateContent?key=gk", captured["url"])
        self.assertIn("contents", captured["payload"])

    def test_openrouter_openai_style(self):
        captured = {}

        def transport(url, headers, payload, timeout):
            captured["url"] = url
            return {"choices": [{"message": {"content": "or ok"}}]}

        p = OpenRouterProvider(
            name="openrouter", endpoint="https://openrouter.ai/api/v1",
            api_key_env="OPENROUTER_API_KEY", transport=transport, environ={},
        )
        resp = p.generate("anthropic/claude-3", "hi")
        self.assertEqual(resp.text, "or ok")
        self.assertEqual(captured["url"], "https://openrouter.ai/api/v1/chat/completions")


class PredictionIntegrationTests(unittest.TestCase):
    def _controller(self):
        engine = AssistantEngine.from_config({}, clock=lambda: 1.0)
        cfg = {"interaction": {"providers": [
            {"name": "xcode", "kind": "xcode", "endpoint": "e", "api_key_env": "XCODE_API_KEY", "enabled": True},
            {"name": "chatgptcodex", "kind": "chatgptcodex", "endpoint": "e", "api_key_env": "OPENAI_API_KEY", "enabled": True},
        ]}}
        return InteractionController.from_config(engine, cfg, environ={}, clock=lambda: 1.0)

    def test_predict_code_via_controller(self):
        ctl = self._controller()
        pred = ctl.predict_code("def f(x): return sorted(x)", filename="s.py")
        self.assertEqual(pred.language, "python")

    def test_predict_records_retention(self):
        ctl = self._controller()
        before = len(ctl.engine.router.retention)
        ctl.predict_code("def f(): pass", filename="f.py")
        self.assertGreater(len(ctl.engine.router.retention), before)

    def test_choose_provider_for_swift_prefers_xcode(self):
        ctl = self._controller()
        pred, provider = ctl.choose_provider_for("func f() { }", filename="v.swift")
        self.assertEqual(pred.language, "swift")
        self.assertEqual(provider, "xcode")

    def test_choose_provider_for_python_prefers_codex(self):
        ctl = self._controller()
        pred, provider = ctl.choose_provider_for("def g(): pass", filename="g.py")
        self.assertEqual(pred.language, "python")
        self.assertEqual(provider, "chatgptcodex")


if __name__ == "__main__":
    unittest.main()
