"""Test the deontic (policy/audit) contextualized translator arm.

The abac theme phrases each formula as a rule the student polices. Per the
Wason selection task literature, facilitation comes from violation-checkable
deontic rules, not from concrete content alone — so this arm differs from
the lights arm in modality and stance, while posing the same formula.

Run with:
    python -m pytest test/test_contextualized_deontic.py -v -s
"""

import unittest
import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import parse_ltl_string
import ltltoeng_prose as prose
import ltltoeng_contextualized as ctx


class TestModalTransform(unittest.TestCase):
    """_modal rewrites copular state phrases into obligations."""

    def test_positive_copula(self):
        self.assertEqual(ctx._modal("the VPN is connected"),
                         "the VPN must be connected")

    def test_negated_copula(self):
        self.assertEqual(ctx._modal("the screen is not shared"),
                         "the screen must not be shared")

    def test_adverb_slots_after_must(self):
        self.assertEqual(ctx._modal("the VPN is connected", "eventually"),
                         "the VPN must eventually be connected")

    def test_adverb_with_negation(self):
        self.assertEqual(ctx._modal("the screen is not shared", "eventually"),
                         "the screen must eventually not be shared")

    def test_never(self):
        self.assertEqual(ctx._modal("the document is open", "never"),
                         "the document must never be open")

    def test_non_copular_fallback(self):
        self.assertEqual(ctx._modal("both conditions hold"),
                         "it must be the case that both conditions hold")


class TestAbacTheme(unittest.TestCase):
    """Exact-sentence checks for the flagship policy skeletons."""

    def setUp(self):
        random.seed(42)
        self.theme = ctx.THEMES["abac"]

    def _tr(self, formula):
        return ctx.translate(parse_ltl_string(formula), self.theme)

    def test_invariant_implication(self):
        self.assertEqual(self._tr("G(d -> v)"),
            "Whenever the document is open, the VPN must be connected.")

    def test_response(self):
        self.assertEqual(self._tr("G(d -> F v)"),
            "Whenever the document is open, the VPN must eventually be connected.")

    def test_mutual_exclusion(self):
        self.assertEqual(self._tr("G !(d & s)"),
            "The document must never be open while the screen is shared.")

    def test_never(self):
        self.assertEqual(self._tr("G !d"),
            "The document must never be open.")

    def test_impossibility(self):
        self.assertEqual(self._tr("!(F d)"),
            "The document must never be open.")

    def test_always(self):
        self.assertEqual(self._tr("G v"),
            "The VPN must always be connected.")

    def test_liveness(self):
        self.assertEqual(self._tr("F v"),
            "The VPN must eventually be connected.")

    def test_until_with_negated_left(self):
        self.assertEqual(self._tr("(!d) U c"),
            "The document must remain closed until the user's clearance is active.")

    def test_negated_consequent_uses_antonym(self):
        self.assertEqual(self._tr("G(s -> !d)"),
            "Whenever the screen is shared, the document must be closed.")

    def test_negated_consequent_without_antonym(self):
        self.assertEqual(self._tr("G(d -> !s)"),
            "Whenever the document is open, the screen must not be shared.")

    def test_immediate_response(self):
        self.assertEqual(self._tr("G(d -> X v)"),
            "Whenever the document is open, the VPN must be connected in the very next step.")

    def test_trigger_stays_indicative(self):
        """Obligation lands on the consequent only — never on the trigger."""
        out = self._tr("G(d -> F v)")
        self.assertTrue(out.startswith("Whenever the document is open,"))
        self.assertNotIn("document must", out)

    def test_persistence(self):
        self.assertEqual(self._tr("G(d -> X d)"),
            "Once the document is open, it must stay that way forever.")

    def test_eventual_stable_response(self):
        self.assertEqual(self._tr("F(G(d -> F v))"),
            "Eventually, the system stabilizes. "
            "From that point on, whenever the document is open, "
            "the VPN must eventually be connected.")

    def test_not_both(self):
        self.assertEqual(self._tr("!(d & s)"),
            "It must not be the case that both the document is open "
            "and the screen is shared.")

    def test_recurrence(self):
        """G carried by the prefix, F by "eventually" — must not read as
        plain G(d), which appears among the distractors."""
        self.assertEqual(self._tr("G(F d)"),
            "No matter how much time passes, the document must eventually be open.")

    def test_recurrence_distinct_from_neighbours(self):
        """The G(F d) sentence must differ from its G(d) and F(d) siblings."""
        recur = self._tr("G(F d)")
        self.assertNotEqual(recur, self._tr("G d"))
        self.assertNotEqual(recur, self._tr("F d"))

    def test_globally_next_single_modal(self):
        self.assertEqual(self._tr("G(X d)"),
            "At every point, the document must be open in the very next step.")

    def test_globally_until_single_modal(self):
        self.assertEqual(self._tr("G(d U c)"),
            "At every point, the document must remain open "
            "until the user's clearance is active.")


class TestLightsUnchanged(unittest.TestCase):
    """Deontic support must not alter the descriptive lights arm: historical
    responses were collected under this exact wording."""

    def _tr(self, formula):
        return ctx.translate(parse_ltl_string(formula), ctx.THEMES["lights"])

    def test_response_unchanged(self):
        self.assertEqual(self._tr("G(b -> F a)"),
            "Whenever the blue light is on, then eventually the amber light is on.")

    def test_never_unchanged(self):
        self.assertEqual(self._tr("G !b"),
            "It is never the case that the blue light is on.")

    def test_until_unchanged(self):
        self.assertEqual(self._tr("(!b) U a"),
            "It must remain the case that the blue light is off until the amber light is on.")


FORMULAS = [
    ("G b",                   "Invariant"),
    ("F b",                   "Liveness"),
    ("G !b",                  "Safety / never"),
    ("G (b -> F a)",          "Response"),
    ("G (b -> X a)",          "Immediate response"),
    ("G(b -> (F a & F p))",   "Chain response"),
    ("G(b -> (a U p))",       "Chain precedence"),
    ("F (G b)",               "Persistence"),
    ("G (F b)",               "Recurrence"),
    ("(G b) U (F a)",         "Obligation until release"),
    ("G(b -> X b)",           "Once true, stays true"),
    ("!(F b)",                "Impossibility"),
    ("b -> a",                "Simple implication"),
    ("G(b -> X(F a))",        "Bounded response"),
    ("F(G(b -> F a))",        "Eventual stable response"),
    ("G((b U a) -> F p)",     "Until-triggered response"),
    ("!(b & a)",              "Mutual exclusion"),
    ("G !(b & a)",            "Mutual exclusion, always"),
]


class TestPrintThreeArms(unittest.TestCase):
    """Print all three experimental arms side by side for eyeballing."""

    def test_print_three_arms(self):
        print("\n" + "=" * 110)
        print("THREE-ARM COMPARISON: abstract / lights (descriptive) / abac (deontic)")
        print("=" * 110)

        for formula_str, desc in FORMULAS:
            random.seed(42)
            abstract = prose.translate(parse_ltl_string(formula_str))
            lights = ctx.translate(parse_ltl_string(formula_str), ctx.THEMES["lights"])
            abac_node = ctx.remap_to_theme(parse_ltl_string(formula_str), ctx.THEMES["abac"])
            abac = ctx.translate(abac_node, ctx.THEMES["abac"]) if abac_node else "(cannot theme)"

            print(f"\n{'─' * 110}")
            print(f"  {formula_str:30s}  ({desc})")
            print(f"{'─' * 110}")
            print(f"  Abstract:  {abstract}")
            print(f"  Lights:    {lights}")
            print(f"  Audit:     {abac}")

        print("\n" + "=" * 110)


if __name__ == "__main__":
    unittest.main()
