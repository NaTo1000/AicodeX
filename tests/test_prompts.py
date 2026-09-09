"""Tests for the six-register prompt registry with simultaneous decipher."""

from __future__ import annotations

import unittest

from edition2.orchestrator import ConfigError
from edition2.prompts import (REGISTER_ALGORITHMS, REGISTER_NAMES,
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


if __name__ == "__main__":
    unittest.main()
