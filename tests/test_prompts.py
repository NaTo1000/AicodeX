"""Tests for the six-register prompt registry with simultaneous decipher."""

from __future__ import annotations

import unittest

from edition2.orchestrator import ConfigError
from edition2.prompts import (LOD_LEVELS, REGISTER_ALGORITHMS, REGISTER_NAMES,
                              PromptRegistry)

DEFS = {
    "R1": {"role": "skeleton_architect", "prompt": "Design the skeleton."},
    "R2": {"role": "formation_planner", "prompt": "Plan the formation."},
    "R3": {"role": "base_coder", "prompt": "Write the base code."},
    "R4": {"role": "error_patcher", "prompt": "Patch the errors."},
    "R5": {"role": "security_netops", "prompt": "Manage security."},
    "R6": {"role": "spec_logger", "prompt": "Log the spec."},
}


class RegisterShapeTests(unittest.TestCase):
    def test_six_registers(self):
        self.assertEqual(len(REGISTER_NAMES), 6)
        self.assertEqual(len(REGISTER_ALGORITHMS), 6)

    def test_registers_are_algorithmically_different(self):
        algorithms = [algo for _, algo in REGISTER_ALGORITHMS]
        self.assertEqual(len(set(algorithms)), 6,
                         "every register must use a different algorithm")

    def test_default_definitions_cover_all_registers(self):
        registry = PromptRegistry(DEFS)
        self.assertEqual(set(registry.algorithms()), set(REGISTER_NAMES))


class RegistrationTests(unittest.TestCase):
    def test_register_commits_all_six(self):
        registry = PromptRegistry(DEFS)
        commitments = registry.register()
        self.assertEqual(len(commitments), 6)

    def test_commitments_use_distinct_digests(self):
        registry = PromptRegistry(DEFS)
        commitments = registry.register()
        digests = [c.digest for c in commitments]
        # All six prompts are distinct, so all six digests are distinct.
        self.assertEqual(len(set(digests)), 6)

    def test_commitment_matches_register_algorithm(self):
        registry = PromptRegistry(DEFS)
        registry.register()
        expected = dict(REGISTER_ALGORITHMS)
        for name in REGISTER_NAMES:
            self.assertEqual(registry.commitment(name).algorithm, expected[name])

    def test_commitment_before_register_raises(self):
        registry = PromptRegistry(DEFS)
        with self.assertRaises(ConfigError):
            registry.commitment("R1")

    def test_invalid_algorithm_rejected(self):
        bad = dict(DEFS)
        bad["R1"] = {"role": "x", "prompt": "y", "algorithm": "not-a-hash"}
        with self.assertRaises(ConfigError):
            PromptRegistry(bad)

    def test_non_object_register_rejected(self):
        with self.assertRaises(ConfigError):
            PromptRegistry({"R1": "oops"})


class DecipherTests(unittest.TestCase):
    def setUp(self):
        self.registry = PromptRegistry(DEFS)
        self.registry.register()

    def test_decipher_recovers_every_role(self):
        result = self.registry.decipher()
        self.assertTrue(result.ok)
        self.assertEqual(len(result.recovered), 6)
        self.assertEqual(set(result.recovered),
                         {d["role"] for d in DEFS.values()})

    def test_decipher_union_never_misses_a_prompt(self):
        result = self.registry.decipher()
        self.assertEqual(set(result.prompts),
                         {d["prompt"] for d in DEFS.values()})

    def test_decipher_auto_registers_when_needed(self):
        registry = PromptRegistry(DEFS)  # never explicitly registered
        result = registry.decipher()
        self.assertTrue(result.ok)
        self.assertEqual(len(result.recovered), 6)

    def test_tampered_register_is_detected_not_missed(self):
        self.registry.tamper("R3", "a different prompt")
        result = self.registry.decipher()
        self.assertFalse(result.ok)
        self.assertEqual(result.mismatched, ["R3"])
        # The other five are still recovered — nothing else is missed.
        self.assertEqual(len(result.recovered), 5)

    def test_dropped_register_is_reported_missing(self):
        self.registry.drop("R5")
        result = self.registry.decipher()
        self.assertFalse(result.ok)
        self.assertEqual(result.missing, ["R5"])
        self.assertEqual(len(result.recovered), 5)

    def test_multiple_failures_all_reported(self):
        self.registry.tamper("R1", "x")
        self.registry.drop("R6")
        result = self.registry.decipher()
        self.assertFalse(result.ok)
        self.assertEqual(result.mismatched, ["R1"])
        self.assertEqual(result.missing, ["R6"])
        self.assertEqual(len(result.recovered), 4)

    def test_decipher_runs_all_registers_at_once(self):
        # All six outcomes are produced from one simultaneous pass.
        result = self.registry.decipher()
        total = (len(result.recovered) + len(result.mismatched)
                 + len(result.missing))
        self.assertEqual(total, 6)


class RenderTests(unittest.TestCase):
    def test_render_lists_registers_and_algorithms(self):
        registry = PromptRegistry(DEFS)
        registry.register()
        text = registry.render()
        for name in REGISTER_NAMES:
            self.assertIn(name, text)
        self.assertIn("distinct algorithms: 6", text)

    def test_render_decipher_ok(self):
        registry = PromptRegistry(DEFS)
        text = registry.render_decipher(registry.decipher())
        self.assertIn("OK — nothing missed", text)

    def test_render_decipher_incomplete(self):
        registry = PromptRegistry(DEFS)
        registry.register()
        registry.drop("R2")
        text = registry.render_decipher(registry.decipher())
        self.assertIn("INCOMPLETE", text)
        self.assertIn("R2", text)


class ParameterTests(unittest.TestCase):
    def test_default_parameters_present(self):
        registry = PromptRegistry(DEFS)
        params = registry.register()[0].parameters
        for key in ("lod", "temperature", "top_p", "max_tokens", "max_bytes"):
            self.assertIn(key, params)

    def test_parameters_fold_into_digest(self):
        a = PromptRegistry(DEFS)
        a.register()
        with_params = dict(DEFS)
        with_params["R1"] = dict(DEFS["R1"], parameters={"temperature": 0.1})
        b = PromptRegistry(with_params)
        b.register()
        self.assertNotEqual(a.commitment("R1").digest, b.commitment("R1").digest)

    def test_invalid_lod_rejected(self):
        bad = dict(DEFS)
        bad["R1"] = dict(DEFS["R1"], parameters={"lod": "ludicrous"})
        with self.assertRaises(ConfigError):
            PromptRegistry(bad)

    def test_numeric_parameters_clamped_to_bounds(self):
        wide = dict(DEFS)
        wide["R1"] = dict(DEFS["R1"], parameters={"temperature": 99.0})
        registry = PromptRegistry(wide)
        registry.register()
        self.assertEqual(registry.parameters("R1")["temperature"], 2.0)


class AlignmentTests(unittest.TestCase):
    def setUp(self):
        self.registry = PromptRegistry(DEFS)
        self.registry.register()

    def test_no_output_means_aligned(self):
        drifts = self.registry.align({})
        self.assertTrue(all(d.aligned for d in drifts))
        self.assertEqual(len(drifts), 6)

    def test_size_blowout_detected(self):
        out = {DEFS["R3"]["role"]: {"bytes_per_output": 999999.0}}
        drifts = self.registry.align(out)
        r3 = next(d for d in drifts if d.register == "R3")
        self.assertTrue(r3.size_blowout)
        self.assertFalse(r3.aligned)

    def test_token_drift_detected(self):
        role = DEFS["R2"]["role"]
        out = {role: {"tokens_per_output": 10.0}}  # way under budget
        drifts = self.registry.align(out)
        r2 = next(d for d in drifts if d.register == "R2")
        self.assertIn("max_tokens", r2.drift)

    def test_temperature_drift_detected(self):
        role = DEFS["R4"]["role"]
        out = {role: {"temperature": 1.8}}
        drifts = self.registry.align(out)
        r4 = next(d for d in drifts if d.register == "R4")
        self.assertIn("temperature", r4.drift)


class FineTuneTests(unittest.TestCase):
    def setUp(self):
        self.registry = PromptRegistry(DEFS)
        self.registry.register()

    def test_fine_tune_noop_when_aligned(self):
        drifts = self.registry.align({})
        changed = self.registry.fine_tune(drifts)
        self.assertEqual(changed, [])

    def test_size_blowout_reduces_lod(self):
        role = DEFS["R3"]["role"]
        drifts = self.registry.align({role: {"bytes_per_output": 999999.0}})
        before = self.registry.parameters("R3")["lod"]
        guidance: list = []
        changed = self.registry.fine_tune(drifts, guidance=guidance)
        after = self.registry.parameters("R3")["lod"]
        self.assertLess(LOD_LEVELS.index(after), LOD_LEVELS.index(before))
        self.assertTrue(any("reduce" in g for g in guidance))
        self.assertTrue(any(c.register == "R3" for c in changed))

    def test_under_budget_extends_lod(self):
        role = DEFS["R2"]["role"]
        drifts = self.registry.align({role: {"tokens_per_output": 5.0}})
        before = self.registry.parameters("R2")["lod"]
        guidance: list = []
        self.registry.fine_tune(drifts, guidance=guidance)
        after = self.registry.parameters("R2")["lod"]
        self.assertGreater(LOD_LEVELS.index(after), LOD_LEVELS.index(before))
        self.assertTrue(any("extend" in g for g in guidance))

    def test_lod_never_below_minimal(self):
        role = DEFS["R1"]["role"]
        params = self.registry.parameters("R1")
        # Drive R1 to minimal, then blow out again — must stay at minimal.
        self.registry._params["R1"]["lod"] = "minimal"
        self.registry.register()
        drifts = self.registry.align({role: {"bytes_per_output": 1e9}})
        self.registry.fine_tune(drifts)
        self.assertEqual(self.registry.parameters("R1")["lod"], "minimal")

    def test_fine_tune_recommits_digests(self):
        role = DEFS["R5"]["role"]
        before = self.registry.commitment("R5").digest
        drifts = self.registry.align({role: {"temperature": 1.9}})
        self.registry.fine_tune(drifts)
        self.assertNotEqual(before, self.registry.commitment("R5").digest)

    def test_guidance_mentions_where_when(self):
        role = DEFS["R3"]["role"]
        drifts = self.registry.align({role: {"bytes_per_output": 1e9}})
        guidance: list = []
        self.registry.fine_tune(drifts, guidance=guidance)
        self.assertTrue(any("when" in g or "where" in g for g in guidance))


if __name__ == "__main__":
    unittest.main()
