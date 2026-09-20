"""Offline crosscode reference, routing, batching, and CLI regression tests."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
from io import StringIO
import json
import math
from pathlib import Path
import threading
import time
import unittest
from unittest.mock import patch

from edition2.__main__ import main
from edition2.chaimera import ConductorX
from edition2.crosscode import CrosscodeMatcher, ReferenceCatalog, MAX_REQUESTS
from edition2.crosscode_catalog import ALGORITHMS, LANGUAGES
from edition2.orchestrator import ConfigError, RoleRegistry, RoleSpec


ROLES = [RoleSpec("test", "Test Model", "metadata only")]
SETTINGS = Path(__file__).resolve().parent.parent / "config" / "edition2_settings.json"


def request(source="python", target="rust", algorithm="integer_sum", **extra):
    return dict(source_lang=source, target_lang=target, algorithm=algorithm, **extra)


def declaration(model_id="custom/id", languages=None, algorithms=None, enabled=True):
    return dict(model_id=model_id, provider="local-declaration",
                languages=languages if languages is not None else list(LANGUAGES),
                algorithms=algorithms if algorithms is not None else list(ALGORITHMS),
                enabled=enabled)


class CatalogTests(unittest.TestCase):
    def test_languages_and_aliases(self):
        catalog = ReferenceCatalog()
        self.assertEqual(len(catalog.describe()["languages"]), 12)
        for language, aliases in LANGUAGES.items():
            for alias in [language] + aliases:
                with self.subTest(alias=alias):
                    self.assertEqual(catalog.canonical(" " + alias.upper() + " "), language)
        self.assertIsNone(catalog.canonical("unknown"))

    def test_all_directed_pairs_and_identity(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        requests = [request(source, target, algorithm)
                    for algorithm in ALGORITHMS
                    for source in LANGUAGES for target in LANGUAGES]
        self.assertEqual(len(requests), 288)
        results = []
        for start in range(0, len(requests), MAX_REQUESTS):
            results.extend(matcher.batch(requests[start:start + MAX_REQUESTS]).results)
        for query, result in zip(requests, results):
            with self.subTest(query=query):
                variants = ALGORITHMS[query["algorithm"]]["variants"]
                self.assertEqual(result.status, "success")
                self.assertEqual(result.source, variants[query["source_lang"]])
                self.assertEqual(result.target, variants[query["target_lang"]])
                self.assertIn("empty", result.semantics)
                self.assertIn("overflow", result.semantics)

    def test_unknown_and_missing_variants_are_unsupported(self):
        algorithms = deepcopy(ALGORITHMS)
        del algorithms["integer_sum"]["variants"]["rust"]
        matcher = CrosscodeMatcher(roles=ROLES, catalog=ReferenceCatalog(algorithms=algorithms))
        report = matcher.batch([
            request(), request("unknown"), request(target="unknown"),
            request(algorithm="sort"), request("rust", "python"),
        ])
        self.assertEqual(report.unsupported, 5)
        self.assertTrue(all(not item.source and not item.target for item in report.results))

    def test_extension_requires_explicit_variants(self):
        languages = dict(LANGUAGES, example=["ex"])
        algorithms = deepcopy(ALGORITHMS)
        algorithms["integer_sum"]["variants"]["example"] = "integer sum reference"
        matcher = CrosscodeMatcher(roles=ROLES, catalog=ReferenceCatalog(languages, algorithms))
        report = matcher.batch([request("EX", "py"), request("py", "ex"),
                                request("ex", "py", "linear_search")])
        self.assertEqual((report.success, report.unsupported), (2, 1))

    def test_catalog_is_defensively_copied(self):
        languages = deepcopy(LANGUAGES)
        algorithms = deepcopy(ALGORITHMS)
        catalog = ReferenceCatalog(languages, algorithms)
        algorithms["integer_sum"]["variants"]["python"] = "changed"
        languages["python"].append("changed")
        description = catalog.describe()
        description["algorithms"].clear()
        self.assertIsNone(catalog.canonical("changed"))
        self.assertEqual(catalog.describe()["algorithms"], ALGORITHMS)

    def test_invalid_catalogs(self):
        invalid = [
            {"languages": []}, {"languages": {}}, {"languages": {"Python": []}},
            {"languages": {"python": "py"}}, {"languages": {"all": []}},
            {"languages": {"python": ["py"], "other": ["PY"]}},
            {"languages": {"python": [None]}}, {"algorithms": []},
            {"algorithms": {"x": {"semantics": "s", "variants": {"unknown": "code"}}}},
            {"algorithms": {"x": {"semantics": "", "variants": {}}}},
            {"algorithms": {"x": {"semantics": "s", "variants": {"python": ""}}}},
            {"algorithms": {"x": {"semantics": "s", "variants": {"python": "x" * 8193}}}},
            {"algorithms": {"x": {"semantics": "s", "variants": []}}},
        ]
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ConfigError):
                ReferenceCatalog(**kwargs)


class ModelTests(unittest.TestCase):
    def test_role_defaults_and_duplicate_labels(self):
        roles = [RoleSpec("a", "Z", "test", enabled=False),
                 RoleSpec("b", "A", "test"), RoleSpec("c", "Z", "test")]
        matcher = CrosscodeMatcher(roles=roles)
        result = matcher.batch([request()]).results[0]
        self.assertEqual(result.eligible_models, ("A", "Z"))
        self.assertEqual(result.selected_model, "A")
        self.assertEqual(result.provider, "configured-role")

    def test_disabled_role_default(self):
        matcher = CrosscodeMatcher(roles=[RoleSpec("a", "Only", "test", enabled=False)])
        self.assertEqual(matcher.batch([request()]).unsupported, 1)

    def test_custom_models_intersection_and_exact_selection(self):
        models = [declaration("Z"), declaration("A"),
                  declaration("source-only", ["py"]),
                  declaration("target-only", ["rs"]),
                  declaration("wrong-algorithm", algorithms=["linear_search"]),
                  declaration("disabled", enabled=False)]
        matcher = CrosscodeMatcher({"models": models}, roles=ROLES)
        report = matcher.batch([request(), request(model="Z"), request(model="disabled"),
                                request(model="unknown"), request(model="source-only"),
                                request(model="Test Model"), request(model="z")])
        self.assertEqual((report.success, report.unsupported), (2, 5))
        self.assertEqual(report.results[0].eligible_models, ("A", "Z"))
        self.assertEqual(report.results[0].selected_model, "A")
        self.assertEqual(report.results[1].selected_model, "Z")

    def test_alias_capabilities_and_config_copy(self):
        models = [declaration(languages=["py", "RS", "python"])]
        matcher = CrosscodeMatcher({"models": models})
        models[0]["enabled"] = False
        models[0]["languages"].clear()
        self.assertEqual(matcher.batch([request()]).success, 1)
        self.assertEqual(matcher.describe()["models"][0]["languages"], ("python", "rust"))

    def test_empty_model_list_replaces_defaults(self):
        matcher = CrosscodeMatcher({"models": []}, roles=ROLES)
        self.assertEqual(matcher.batch([request()]).unsupported, 1)

    def test_models_are_order_independent(self):
        models = [declaration("Z"), declaration("A")]
        a = CrosscodeMatcher({"models": models}).batch([request()]).results
        b = CrosscodeMatcher({"models": list(reversed(models))}).batch([request()]).results
        self.assertEqual(a, b)

    def test_malformed_model_configuration(self):
        mutations = [
            {"model_id": ""}, {"model_id": 2}, {"model_id": "x" * 129},
            {"provider": None}, {"enabled": "true"}, {"enabled": 1},
            {"languages": "python"}, {"languages": [None]}, {"languages": ["unknown"]},
            {"algorithms": ["sort"]}, {"algorithms": {}}, {"endpoint": "not-allowed"},
        ]
        for mutation in mutations:
            model = declaration()
            model.update(mutation)
            with self.subTest(mutation=mutation), self.assertRaises(ConfigError):
                CrosscodeMatcher({"models": [model]})
        for models in (None, {}, [None], [declaration(), declaration()], [declaration()] * 257):
            with self.subTest(models=models), self.assertRaises(ConfigError):
                CrosscodeMatcher({"models": models})


class BatchTests(unittest.TestCase):
    def test_order_metrics_and_determinism(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        requests = [request(target=language) for language in reversed(LANGUAGES)]
        requests.append(request(target="unknown"))
        with patch("edition2.crosscode.perf_counter", side_effect=[10.0, 10.5]):
            report = matcher.batch(requests)
        self.assertEqual([r.target_lang for r in report.results],
                         [r["target_lang"] for r in requests])
        self.assertEqual((report.success, report.unsupported), (12, 1))
        self.assertEqual(report.configured_max_workers, 4)
        self.assertEqual(report.concurrency, 4)
        self.assertEqual(report.elapsed_s, 0.5)
        self.assertEqual(report.requests_per_second, 26)
        self.assertEqual(report.results, matcher.batch(requests, workers=1).results)
        self.assertEqual(len(json.loads(json.dumps(report.as_dict()))["results"]), 13)

    def test_measured_concurrency_obeys_config_and_caller(self):
        for bound, requested, expected in ((2, 256, 2), (4, 1, 1), (4, None, 4)):
            with self.subTest(bound=bound, requested=requested):
                matcher = CrosscodeMatcher({"max_workers": bound}, roles=ROLES)
                lock = threading.Lock()
                active = peak = 0
                rendezvous = threading.Barrier(expected)
                match = matcher._match

                def measured(query):
                    nonlocal active, peak
                    with lock:
                        active += 1
                        peak = max(active, peak)
                    try:
                        rendezvous.wait(timeout=5)
                        time.sleep(0.005)
                        return match(query)
                    finally:
                        with lock:
                            active -= 1

                with patch.object(matcher, "_match", side_effect=measured):
                    report = matcher.batch([request()] * 8, workers=requested)
                self.assertEqual(peak, expected)
                self.assertEqual(report.concurrency, expected)
                self.assertEqual(active, 0)

    def test_controller_is_used_and_small_batch_bound(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        with patch.object(matcher._performance, "effective_workers",
                          wraps=matcher._performance.effective_workers) as effective:
            report = matcher.batch([request()], workers=200)
        effective.assert_called_once_with(1, 200)
        self.assertEqual(report.concurrency, 1)

    def test_empty_batch_does_not_allocate_executor(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        with patch("edition2.crosscode.ThreadPoolExecutor") as executor:
            report = matcher.batch([])
        executor.assert_not_called()
        self.assertEqual((report.success, report.unsupported, report.concurrency), (0, 0, 0))
        self.assertEqual(report.requests_per_second, 0)
        self.assertGreaterEqual(report.elapsed_s, 0)
        self.assertTrue(math.isfinite(report.elapsed_s))

    def test_all_targets_sorted_and_excludes_source_alias(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        report = matcher.batch([request("PY", "ALL")])
        self.assertEqual([r.target_lang for r in report.results],
                         sorted(set(LANGUAGES) - {"python"}))
        self.assertEqual(report.success, 11)
        self.assertEqual(matcher.batch([request("unknown", "all")]).unsupported, 12)

    def test_batch_limit_including_expansion(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        self.assertEqual(matcher.batch([request()] * 256).success, 256)
        for requests in ([request()] * 257, [request(target="all")] * 24):
            with self.assertRaises(ConfigError):
                matcher.batch(requests)

    def test_invalid_workers_are_strict_even_for_empty_batch(self):
        bad = (0, -1, True, False, 1.0, 1.5, float("nan"), float("inf"), "4", [], {})
        for value in bad + (33, None):
            with self.subTest(config=value), self.assertRaises(ConfigError):
                CrosscodeMatcher({"max_workers": value})
        matcher = CrosscodeMatcher(roles=ROLES)
        for value in bad + (257,):
            with self.subTest(request=value), self.assertRaises(ConfigError):
                matcher.batch([], workers=value)
        self.assertEqual(CrosscodeMatcher({"max_workers": 32}, roles=ROLES).max_workers, 32)

    def test_invalid_requests_are_rejected_before_matching(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        invalid = (None, {}, "request", [None], [{}], [request(source=1)],
                   [request(target="")], [request(algorithm="x" * 129)],
                   [request(model=None)], [request(model="")],
                   [request(source="py\n")], [request(code="arbitrary program")])
        for requests in invalid:
            with self.subTest(requests=requests), patch.object(matcher, "_match") as match:
                with self.assertRaises(ConfigError):
                    matcher.batch(requests)
                match.assert_not_called()

    def test_malformed_config(self):
        for config in (None, [], "", {"workers": 4}, {"requests": None},
                       {"requests": [{}]}, {"requests": [request()] * 257}):
            with self.subTest(config=config), self.assertRaises(ConfigError):
                CrosscodeMatcher(config, roles=ROLES)

    def test_no_execution_or_io_during_matching(self):
        matcher = CrosscodeMatcher(roles=ROLES)
        with patch("builtins.open", side_effect=AssertionError("I/O")), \
                patch("builtins.eval", side_effect=AssertionError("eval")), \
                patch("builtins.exec", side_effect=AssertionError("exec")), \
                patch("subprocess.Popen", side_effect=AssertionError("subprocess")), \
                patch("socket.socket", side_effect=AssertionError("network")):
            self.assertEqual(matcher.batch([request()]).success, 1)


class CLITests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads(SETTINGS.read_text(encoding="utf-8"))

    def cli(self, *args):
        stdout, stderr = StringIO(), StringIO()
        with patch("edition2.__main__._load_config", return_value=self.config), \
                redirect_stdout(stdout), redirect_stderr(stderr):
            try:
                status = main(list(args))
            except SystemExit as exc:
                status = exc.code
        return status, stdout.getvalue(), stderr.getvalue()

    def test_json_match_all_and_exact_model(self):
        status, output, error = self.cli("--crosscode", "py", "all", "integer_sum",
                                         "--crosscode-json", "--crosscode-workers", "256",
                                         "--crosscode-model", "Claude")
        self.assertEqual((status, error), (0, ""))
        report = json.loads(output)
        self.assertEqual((report["success"], report["concurrency"]), (11, 4))
        self.assertTrue(all(item["selected_model"] == "Claude" for item in report["results"]))

    def test_catalog_and_text(self):
        for flags in (("--crosscode-catalog",),
                      ("--crosscode", "ruby", "c#", "linear_search")):
            status, output, error = self.cli(*flags)
            self.assertEqual((status, error), (0, ""))
            self.assertIn("linear_search", output)
            self.assertIn("declaration", output)
        status, output, _ = self.cli("--crosscode-catalog", "--crosscode-json")
        self.assertEqual(status, 0)
        self.assertEqual(len(json.loads(output)["languages"]), 12)

    def test_unsupported_exit_and_json(self):
        for query in (("unknown", "rust", "integer_sum"),
                      ("python", "rust", "unknown")):
            status, output, error = self.cli("--crosscode", *query, "--crosscode-json")
            self.assertEqual((status, error), (1, ""))
            self.assertEqual(json.loads(output)["unsupported"], 1)
        status, output, _ = self.cli("--crosscode", "py", "rs", "integer_sum",
                                     "--crosscode-model", "not-configured")
        self.assertEqual(status, 1)
        self.assertIn("Requested model", output)

    def test_invalid_config_controlled_on_base_and_query(self):
        for malformed in (None, [], {"max_workers": True}, {"max_workers": float("nan")},
                          {"requests": [{}]}, {"models": [{"model_id": "bad"}]}):
            self.config["crosscode"] = malformed
            for args in ((), ("--crosscode", "py", "rs", "integer_sum")):
                with self.subTest(config=malformed, args=args):
                    status, output, error = self.cli(*args)
                    self.assertEqual((status, output), (2, ""))
                    self.assertIn("error:", error)
                    self.assertNotIn("Traceback", error)

    def test_modifiers_and_mode_conflicts(self):
        invalid = [
            ("--crosscode-json",), ("--crosscode-model", "Claude"),
            ("--crosscode-workers", "2"), ("--version", "--crosscode-json"),
            ("--crosscode-catalog", "--crosscode-workers", "2"),
            ("--crosscode", "py", "rs", "integer_sum", "--crosscode-catalog"),
            ("--crosscode", "py", "rs", "integer_sum", "--crossover"),
            ("--crosscode", "py", "rs", "integer_sum", "--style-fingerprint", ""),
            ("--crosscode", "py", "rs", "integer_sum", "--crosscode-workers", "1.5"),
            ("--crosscode", "py", "rs", "integer_sum", "--crosscode-workers", "0"),
            ("--crosscode", "py", "rs", "integer_sum", "--crosscode-workers", "257"),
        ]
        for args in invalid:
            with self.subTest(args=args):
                status, output, error = self.cli(*args)
                self.assertEqual((status, output), (2, ""))
                self.assertIn("error:", error)

    def test_base_output_unchanged_with_empty_or_absent_requests(self):
        expected = ConductorX(RoleRegistry(self.config["roles"])).conduct(
            seeds=set(self.config["orchestration"]["seeds"])).render() + "\n"
        for with_config in (True, False):
            if not with_config:
                del self.config["crosscode"]
            status, output, error = self.cli()
            self.assertEqual((status, output, error), (0, expected, ""))

    def test_base_opt_in_appends_references_and_propagates_failure(self):
        self.config["crosscode"]["requests"] = [request()]
        status, output, error = self.cli()
        self.assertEqual((status, error), (0, ""))
        self.assertIn("Symphony", output)
        self.assertIn("Crosscode", output)
        self.assertIn("success=1 unsupported=0", output)
        self.config["crosscode"]["requests"] = [request(algorithm="unknown")]
        self.assertEqual(self.cli()[0], 1)

    def test_legacy_crossover_unchanged(self):
        status, output, error = self.cli("--crossover")
        self.assertEqual((status, error), (0, ""))
        self.assertIn("entries: 4", output)
        self.assertNotIn("integer_sum", output)


if __name__ == "__main__":
    unittest.main()
