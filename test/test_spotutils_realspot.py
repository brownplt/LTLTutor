"""Real-SPOT tests for spotutils.py.

Unlike almost every other test file in this suite, this one deliberately does
**not** mock the ``spot`` module. Historically every test replaced ``spot`` with
a ``MagicMock`` so the suite could run in environments where the (conda-only)
SPOT library is absent. The unfortunate side effect is that ``spotutils.py`` --
the module whose failures cause blank exercises and 500s in front of a live
classroom (see ENGINEERING-DEBT.md sec.5) -- was never actually exercised.

These tests run against the real SPOT kernel. They are skipped automatically if
SPOT is not importable, so they stay green in a minimal local environment while
providing a genuine safety net in Docker/CI where SPOT is present.

Robustness note: because sibling test files install ``sys.modules['spot'] =
MagicMock()`` at import time, we pop and re-import the real modules here. This
pattern has been verified to coexist with the mocking suite under both
``pytest`` and ``unittest discover`` regardless of collection order.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import realspot

_loaded = realspot.load_real("spotutils")
SPOT_AVAILABLE = _loaded is not None
if SPOT_AVAILABLE:
    (spotutils,) = _loaded


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestEquivalenceAndRelations(unittest.TestCase):
    def test_areEquivalent_true_for_semantically_equal_formulas(self):
        self.assertIs(spotutils.areEquivalent("G a", "G G a"), True)
        self.assertIs(spotutils.areEquivalent("a", "a"), True)
        # F F a === F a
        self.assertIs(spotutils.areEquivalent("F a", "F F a"), True)

    def test_areEquivalent_false_for_distinct_formulas(self):
        self.assertIs(spotutils.areEquivalent("G a", "F a"), False)
        self.assertIs(spotutils.areEquivalent("a", "X a"), False)

    def test_isSufficientFor_is_one_directional_implication(self):
        # G a  =>  a   (holds), but  a  does NOT imply  G a
        self.assertIs(spotutils.isSufficientFor("G a", "a"), True)
        self.assertIs(spotutils.isSufficientFor("a", "G a"), False)
        # a & b  =>  a
        self.assertIs(spotutils.isSufficientFor("a & b", "a"), True)

    def test_isNecessaryFor_is_the_reverse_of_isSufficientFor(self):
        # isNecessaryFor(f, g) == isSufficientFor(g, f)
        self.assertEqual(
            spotutils.isNecessaryFor("a", "G a"),
            spotutils.isSufficientFor("G a", "a"),
        )
        self.assertIs(spotutils.isNecessaryFor("a", "G a"), True)

    def test_areEquivalent_iff_sufficient_and_necessary(self):
        for f, g in [("G a", "G G a"), ("G a", "F a"), ("a & b", "b & a"), ("a", "X a")]:
            expected = spotutils.isSufficientFor(f, g) and spotutils.isNecessaryFor(f, g)
            self.assertEqual(spotutils.areEquivalent(f, g), bool(expected), f"{f} vs {g}")

    def test_areDisjoint(self):
        # a and !a can never both hold -> disjoint
        self.assertIs(spotutils.areDisjoint("a", "! a"), True)
        # a and b CAN both hold (a & b) -> not disjoint
        self.assertIs(spotutils.areDisjoint("a", "b"), False)


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestTraceSatisfaction(unittest.TestCase):
    def test_globally_satisfaction(self):
        self.assertTrue(spotutils.is_trace_satisfied(trace="cycle{a}", formula="G a"))
        # a fails in the first state -> G a not satisfied
        self.assertFalse(spotutils.is_trace_satisfied(trace="! a; cycle{a}", formula="G a"))

    def test_eventually_satisfaction(self):
        self.assertTrue(spotutils.is_trace_satisfied(trace="! a; ! a; cycle{a}", formula="F a"))
        self.assertFalse(spotutils.is_trace_satisfied(trace="cycle{! a}", formula="F a"))

    def test_returns_plain_bool(self):
        result = spotutils.is_trace_satisfied(trace="cycle{a}", formula="G a")
        self.assertIsInstance(result, bool)


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestTrivialityDetection(unittest.TestCase):
    def test_tautologies_and_contradictions_are_trivial(self):
        self.assertTrue(spotutils.is_trivial("a | !a"))   # tautology
        self.assertTrue(spotutils.is_trivial("a & !a"))   # contradiction
        self.assertTrue(spotutils.is_trivial("true"))
        self.assertTrue(spotutils.is_trivial("false"))

    def test_contingent_formulas_are_not_trivial(self):
        self.assertFalse(spotutils.is_trivial("a"))
        self.assertFalse(spotutils.is_trivial("G a"))
        self.assertFalse(spotutils.is_trivial("a U b"))

    def test_is_trivial_never_raises_even_on_garbage(self):
        # is_trivial has a bare try/except and must swallow parse errors.
        self.assertFalse(spotutils.is_trivial("@@@ not a formula @@@"))


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestTraceGeneration(unittest.TestCase):
    def test_generated_traces_actually_satisfy_the_formula(self):
        # The strongest possible property for a trace generator: every trace it
        # emits for a formula must in fact satisfy that formula. This exercises
        # generation AND satisfaction together and is insensitive to SPOT's
        # exact string formatting.
        for formula in ["G a", "F a", "a U b", "X a", "G (a -> F b)"]:
            traces = spotutils.generate_accepted_traces(formula, max_traces=4)
            self.assertGreater(len(traces), 0, f"no traces generated for {formula}")
            for trace in traces:
                self.assertTrue(
                    spotutils.is_trace_satisfied(trace=trace, formula=formula),
                    f"generated trace {trace!r} does NOT satisfy {formula!r}",
                )

    def test_generated_traces_are_distinct(self):
        traces = spotutils.generate_accepted_traces("F a", max_traces=5)
        self.assertEqual(len(traces), len(set(traces)))

    def test_generate_traces_respects_accept_and_reject(self):
        # Each trace must satisfy f_accepted and must NOT satisfy f_rejected.
        f_accepted, f_rejected = "F a", "G ! a"
        traces = spotutils.generate_traces(f_accepted, f_rejected, max_traces=4)
        self.assertGreater(len(traces), 0)
        for trace in traces:
            self.assertTrue(spotutils.is_trace_satisfied(trace=trace, formula=f_accepted))
            self.assertFalse(spotutils.is_trace_satisfied(trace=trace, formula=f_rejected))

    def test_max_traces_is_an_upper_bound(self):
        self.assertLessEqual(len(spotutils.generate_accepted_traces("F a", max_traces=2)), 2)


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestClassificationHelpers(unittest.TestCase):
    def test_mana_pnueli_classification(self):
        # These are stable Manna-Pnueli class names from SPOT's mp_class(f, 'v').
        self.assertEqual(spotutils.get_mana_pneulli_class("G a"), "safety")
        self.assertEqual(spotutils.get_mana_pneulli_class("F a"), "guarantee")
        self.assertEqual(spotutils.get_mana_pneulli_class("G F a"), "recurrence")
        self.assertEqual(spotutils.get_mana_pneulli_class("F G a"), "persistence")

    def test_get_aut_size_is_positive_int(self):
        size = spotutils.get_aut_size("G a")
        self.assertIsInstance(size, int)
        self.assertGreaterEqual(size, 1)


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestMalformedInputContract(unittest.TestCase):
    """Characterization of how SPOT wrappers behave on malformed input.

    IMPORTANT: these tests document the *current* contract, which is that most
    wrappers propagate SPOT's ``SyntaxError`` rather than degrading gracefully.
    This is ENGINEERING-DEBT.md sec.5 ("SPOT Error Handling", severity High):
    unguarded failures surface as blank exercises / 500s in a live classroom.

    If/when these functions are hardened to return safe defaults (None / []),
    THESE tests should be updated to assert the graceful behavior -- they exist
    precisely so that such a change is a conscious, reviewed decision and not an
    accident. Only ``is_trivial`` currently guards its own parsing.
    """

    def test_is_trace_satisfied_raises_on_malformed_formula(self):
        with self.assertRaises(Exception):
            spotutils.is_trace_satisfied(trace="cycle{a}", formula="@@@")

    def test_is_trace_satisfied_raises_on_malformed_trace(self):
        with self.assertRaises(Exception):
            spotutils.is_trace_satisfied(trace="not-a-trace", formula="G a")

    def test_relation_helpers_raise_on_malformed_formula(self):
        with self.assertRaises(Exception):
            spotutils.isSufficientFor("@@@", "a")

    def test_trace_generation_raises_on_malformed_formula(self):
        with self.assertRaises(Exception):
            spotutils.generate_accepted_traces("@@@", max_traces=3)

    def test_mp_class_raises_on_malformed_formula(self):
        with self.assertRaises(Exception):
            spotutils.get_mana_pneulli_class("@@@")


if __name__ == "__main__":
    unittest.main()
