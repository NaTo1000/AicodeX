"""
Tests for the Assistant Persona & Analysis Engine (Python core).
"""

import os
import sys
import unittest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from assistant import (
    AssistantEngine,
    CorpusCallosumCouncil,
    IncomingDataAnalyzer,
    KnowledgeEntry,
    Pathway,
    PersonaStyle,
    PECRouter,
    RetentionStore,
    SolutionMatcher,
    TermControl,
    TwinBrain,
)


class PersonaStyleTests(unittest.TestCase):
    def test_default_persona(self):
        p = PersonaStyle.default()
        self.assertEqual(p.tone, "analytical")
        self.assertAlmostEqual(p.trait("analytical"), 0.9)

    def test_traits_are_clamped(self):
        p = PersonaStyle(traits={"analytical": 5.0, "creative": -2.0})
        self.assertEqual(p.trait("analytical"), 1.0)
        self.assertEqual(p.trait("creative"), 0.0)

    def test_merge_fine_tunes_single_axis(self):
        p = PersonaStyle.default()
        tuned = p.merge({"tone": "creative", "traits": {"creative": 0.95}})
        self.assertEqual(tuned.tone, "creative")
        self.assertEqual(tuned.trait("creative"), 0.95)
        # Untouched axes are preserved.
        self.assertEqual(tuned.trait("analytical"), p.trait("analytical"))
        # Original is unchanged (immutability of fine-tune).
        self.assertEqual(p.trait("creative"), 0.4)

    def test_from_config(self):
        p = PersonaStyle.from_config({"name": "X", "tone": "driver", "traits": {"driver": 1.0}})
        self.assertEqual(p.name, "X")
        self.assertEqual(p.trait("driver"), 1.0)

    def test_dominant_traits_sorted(self):
        p = PersonaStyle(traits={"a": 0.2, "b": 0.9, "c": 0.5})
        self.assertEqual([a for a, _ in p.dominant_traits()], ["b", "c", "a"])


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.analyzer = IncomingDataAnalyzer()

    def test_analytical_text_scores_analytical(self):
        profile = self.analyzer.analyze(
            "analyze the benchmark data and measure the root cause with evidence"
        )
        self.assertEqual(profile.dominant(), "analytical")
        self.assertGreater(profile.confidence, 0.0)

    def test_driver_text(self):
        profile = self.analyzer.analyze("ship it asap, deliver results, decide now")
        self.assertEqual(profile.dominant(), "driver")

    def test_empty_input_zero_confidence(self):
        profile = self.analyzer.analyze("")
        self.assertEqual(profile.confidence, 0.0)
        self.assertEqual(profile.token_count, 0)

    def test_noise_input_zero_confidence(self):
        profile = self.analyzer.analyze("zzqq xxww vvuu")
        self.assertEqual(profile.confidence, 0.0)

    def test_scores_normalise_to_distribution(self):
        profile = self.analyzer.analyze("analyze data and create a design with the team")
        total = sum(profile.scores.values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_non_string_input_flattened(self):
        profile = self.analyzer.analyze({"goal": "analyze the data", "other": ["measure"]})
        self.assertGreater(profile.scores.get("analytical", 0.0), 0.0)


class SolutionMatcherTests(unittest.TestCase):
    def setUp(self):
        self.kb = [
            KnowledgeEntry("perf-analytical", "Profile then optimize.", {"analytical": 0.5}, 0.5),
            KnowledgeEntry("perf-driver", "Cut scope and ship.", {"driver": 0.5}, 0.4),
        ]
        self.matcher = SolutionMatcher(self.kb)
        self.analyzer = IncomingDataAnalyzer()

    def test_matches_fitting_profile(self):
        profile = self.analyzer.analyze("analyze the data and measure everything with benchmarks and logic")
        match = self.matcher.match(profile)
        self.assertTrue(match.matched)
        self.assertEqual(match.entry.id, "perf-analytical")
        self.assertTrue(match.solution)

    def test_empty_knowledge_base_explains(self):
        matcher = SolutionMatcher([])
        profile = self.analyzer.analyze("analyze the data")
        match = matcher.match(profile)
        self.assertFalse(match.matched)
        self.assertIn("No performance solutions are configured", match.explanation)

    def test_low_confidence_explains_why(self):
        profile = self.analyzer.analyze("zzqq nothing meaningful")
        match = self.matcher.match(profile)
        self.assertFalse(match.matched)
        self.assertIn("confidence", match.explanation.lower())

    def test_unmet_traits_reported(self):
        # Text that is partly analytical but doesn't meet the full requirement.
        profile = self.analyzer.analyze("analyze this a bit")
        match = self.matcher.match(profile)
        if not match.matched:
            self.assertTrue(match.explanation)


class TwinBrainCouncilTests(unittest.TestCase):
    def test_two_hemispheres_proposed(self):
        persona = PersonaStyle.default()
        brain = TwinBrain(persona)
        analyzer = IncomingDataAnalyzer()
        matcher = SolutionMatcher([
            KnowledgeEntry("perf-driver", "Ship the smallest change.", {"driver": 0.5}, 0.4)
        ])
        profile = analyzer.analyze("ship it asap, deliver results fast, decide now, win")
        match = matcher.match(profile)
        pathways = brain.propose("q", profile, match)
        self.assertEqual(len(pathways), 2)
        self.assertEqual({p.hemisphere for p in pathways}, {"left", "right"})

    def test_council_selects_highest_score(self):
        council = CorpusCallosumCouncil(min_confidence=0.5, min_justification=0.4)
        strong = Pathway("left", "A", "r", evidence=0.9)
        weak = Pathway("right", "B", "r", evidence=0.2)
        decision = council.deliberate([weak, strong], profile_confidence=0.8)
        self.assertEqual(decision.chosen.title, "A")
        self.assertTrue(decision.justified)

    def test_council_marks_unjustified_when_gates_fail(self):
        council = CorpusCallosumCouncil(min_confidence=0.5, min_justification=0.4)
        weak = Pathway("right", "B", "r", evidence=0.1)
        decision = council.deliberate([weak], profile_confidence=0.2)
        self.assertFalse(decision.justified)
        self.assertIn("cannot assert", decision.justification)

    def test_council_empty_pathways(self):
        council = CorpusCallosumCouncil()
        decision = council.deliberate([], profile_confidence=0.5)
        self.assertIsNone(decision.chosen)
        self.assertFalse(decision.justified)

    def test_retained_prior_nudges_confidence(self):
        council = CorpusCallosumCouncil(min_confidence=0.5, min_justification=0.4)
        p = Pathway("left", "A", "r", evidence=0.9)
        low = council.deliberate([p], profile_confidence=0.4, retained_prior=None)
        boosted = council.deliberate([p], profile_confidence=0.4, retained_prior=1.0)
        self.assertGreater(boosted.confidence, low.confidence)


class RouterRetentionTests(unittest.TestCase):
    def test_term_control_strips_stop_words(self):
        tc = TermControl()
        terms = tc.controlled_terms("the quick brown fox and the slow dog")
        self.assertIn("quick", terms)
        self.assertNotIn("the", terms)
        self.assertNotIn("and", terms)

    def test_retention_records_and_prior(self):
        store = RetentionStore(enabled=True, max_records=10, clock=lambda: 1.0)
        store.record("k", "q1", "A", True, 0.8)
        store.record("k", "q2", "A", False, 0.4)
        prior = store.prior("k")
        self.assertIsNotNone(prior)
        self.assertTrue(0.0 <= prior <= 1.0)
        self.assertIsNone(store.prior("missing"))

    def test_retention_bounded(self):
        store = RetentionStore(enabled=True, max_records=3, clock=lambda: 1.0)
        for i in range(5):
            store.record("k", f"q{i}", "A", True, 0.5)
        self.assertEqual(len(store), 3)

    def test_retention_disabled(self):
        store = RetentionStore(enabled=False)
        store.record("k", "q", "A", True, 0.5)
        self.assertEqual(len(store), 0)

    def test_router_spread_channels(self):
        router = PECRouter()
        result = router.spread("analyze the data and measure performance")
        self.assertEqual(result.channels, ["analysis", "solutions", "twinbrain", "council"])
        self.assertTrue(result.terms)


class EngineIntegrationTests(unittest.TestCase):
    def _engine(self):
        return AssistantEngine.from_config({}, clock=lambda: 1.0)

    def test_process_returns_full_report(self):
        eng = self._engine()
        report = eng.process("analyze the benchmark data and measure the root cause")
        self.assertTrue(report.summary())
        data = report.as_dict()
        for key in ("persona", "profile", "match", "pathways", "decision", "routing"):
            self.assertIn(key, data)
        self.assertEqual(len(report.pathways), 2)

    def test_process_records_return(self):
        eng = self._engine()
        eng.process("analyze the data and measure it")
        self.assertGreaterEqual(len(eng.router.retention), 1)

    def test_process_noise_explains(self):
        eng = self._engine()
        report = eng.process("zzqq xxww")
        self.assertFalse(report.match.matched)
        self.assertIn("No solution", report.summary())

    def test_fine_tune_returns_new_engine(self):
        eng = self._engine()
        tuned = eng.fine_tune({"tone": "creative", "traits": {"creative": 0.99}})
        self.assertEqual(tuned.persona.tone, "creative")
        self.assertEqual(tuned.persona.trait("creative"), 0.99)
        # Original engine persona untouched.
        self.assertEqual(eng.persona.tone, "analytical")


if __name__ == "__main__":
    unittest.main()
