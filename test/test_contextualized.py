"""Test the contextualized (Wason-style) LTL translator.

Run with:
    python -m pytest test/test_contextualized.py -v -s
"""

import unittest
import sys
import os
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import parse_ltl_string
import ltltoeng
import ltltoeng_prose as prose
import ltltoeng_contextualized as ctx


FORMULAS = [
    # (formula, description)
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
]


class TestContextualizedPrintComparison(unittest.TestCase):
    """Print abstract vs. contextualized (lights) translations."""

    def setUp(self):
        random.seed(42)

    def test_print_all_themes(self):
        print("\n" + "=" * 110)
        print("ABSTRACT vs. CONTEXTUALIZED TRANSLATIONS  (Wason-style)")
        print("=" * 110)

        for formula_str, desc in FORMULAS:
            random.seed(42)
            abstract = prose.translate(parse_ltl_string(formula_str))
            lights   = ctx.translate(parse_ltl_string(formula_str), ctx.THEMES["lights"])

            print(f"\n{'─' * 110}")
            print(f"  {formula_str:30s}  ({desc})")
            print(f"{'─' * 110}")
            print(f"  Abstract:  {abstract}")
            print(f"  Lights:    {lights}")

        print("\n" + "=" * 110)


class TestLightsTheme(unittest.TestCase):
    """Verify the lights theme produces concrete, accurate translations."""

    def setUp(self):
        random.seed(42)
        self.theme = ctx.THEMES["lights"]

    def _tr(self, formula):
        return ctx.translate(parse_ltl_string(formula), self.theme)

    def test_globally_literal(self):
        result = self._tr("G b")
        self.assertIn("blue light", result.lower())
        self.assertIn("all times", result.lower())

    def test_finally_literal(self):
        result = self._tr("F b")
        self.assertIn("blue light", result.lower())
        self.assertIn("eventually", result.lower())

    def test_never(self):
        result = self._tr("G !b")
        self.assertIn("blue light", result.lower())
        self.assertIn("never", result.lower())

    def test_response_uses_state_phrasing(self):
        """G(b -> F a) triggers in every state where b holds, so the
        antecedent must be phrased as a state ('is on'), never as an
        event ('turns on')."""
        result = self._tr("G(b -> F a)")
        self.assertIn("blue light is on", result.lower())
        self.assertIn("amber light", result.lower())
        self.assertIn("eventually", result.lower())

    def test_immediate_response(self):
        result = self._tr("G(b -> X a)")
        self.assertIn("blue light is on", result.lower())
        self.assertIn("amber light", result.lower())
        self.assertIn("next step", result.lower())

    def test_no_event_phrasing_anywhere(self):
        """A bare LTL literal has state semantics: it holds in every state
        where it is true, not only on a false->true transition. Event
        phrasing would describe a different formula — e.g. a trace where
        blue starts on and stays on satisfies the trigger of G(b -> F a)
        even though blue never 'turns on' — corrupting both grading and
        the A/B comparison."""
        for formula_str, _ in FORMULAS:
            result = self._tr(formula_str)
            for phrase in ["turns on", "turns off", "becomes", "happens"]:
                self.assertNotIn(
                    phrase, result.lower(),
                    f"{formula_str} => event phrasing '{phrase}': {result}")

    def test_chain_response_mentions_both(self):
        result = self._tr("G(b -> (F a & F p))")
        self.assertIn("blue light", result.lower())
        self.assertIn("amber light", result.lower())
        self.assertIn("purple light", result.lower())

    def test_persistence(self):
        result = self._tr("G(b -> X b)")
        self.assertIn("blue light", result.lower())
        self.assertIn("forever", result.lower())

    def test_recurrence(self):
        """G and F must be carried by separate phrases: a single continuity
        idiom ("over and over") reads as plain G and collides with the G(p)
        distractor."""
        result = self._tr("G(F b)")
        self.assertEqual(result,
            "No matter how much time passes, eventually the blue light is on.")

    def test_mutual_exclusion(self):
        result = self._tr("!(b & a)")
        self.assertIn("blue light", result.lower())
        self.assertIn("amber light", result.lower())

    def test_all_end_with_period(self):
        for formula_str, _ in FORMULAS:
            result = self._tr(formula_str)
            self.assertTrue(result.endswith("."),
                            f"{formula_str} => '{result}' missing period")

    def test_all_start_capitalized(self):
        for formula_str, _ in FORMULAS:
            result = self._tr(formula_str)
            self.assertTrue(result[0].isupper(),
                            f"{formula_str} => '{result}' not capitalized")

    def test_no_abstract_quotes(self):
        """Contextualized output should never contain raw quoted literals."""
        for formula_str, _ in FORMULAS:
            result = self._tr(formula_str)
            for lit in ["'b'", "'a'", "'p'", "'c'"]:
                self.assertNotIn(lit, result,
                                 f"{formula_str} => still has abstract literal {lit}: {result}")

    def test_theme_literals_avoid_operator_letters(self):
        """Theme literals must stay clear of letters that look like LTL
        operators (F, G, M, R, U, W, X), matching the tutor's exercise
        literal pool."""
        operator_lookalikes = set("fgmruwx")
        for lit in self.theme.literals:
            self.assertNotIn(lit, operator_lookalikes)


class TestRemapToTheme(unittest.TestCase):
    """Verify remapping arbitrary formulas onto the lights theme."""

    def test_remaps_foreign_literals(self):
        node = parse_ltl_string("G(z -> F k)")
        remapped = ctx.remap_to_theme(node)
        self.assertIsNotNone(remapped)
        lits = ctx.collect_literals(remapped)
        self.assertTrue(lits.issubset(set(ctx.THEMES["lights"].literals)))

    def test_preserves_theme_literals(self):
        """Literals already in the theme keep their names."""
        node = parse_ltl_string("G(b -> F z)")
        remapped = ctx.remap_to_theme(node)
        lits = ctx.collect_literals(remapped)
        self.assertIn("b", lits)
        self.assertEqual(len(lits), 2)

    def test_preserves_structure(self):
        """Renaming must not change the formula shape."""
        node = parse_ltl_string("G(z -> (k U j))")
        original_shape = str(node)
        remapped = ctx.remap_to_theme(node)
        # Same operator skeleton: replace literals with a placeholder
        import re
        skeleton = lambda s: re.sub(r'\b[a-z]\b', '#', s)
        self.assertEqual(skeleton(original_shape), skeleton(str(remapped)))

    def test_deterministic(self):
        a = str(ctx.remap_to_theme(parse_ltl_string("G(z -> F k)")))
        b = str(ctx.remap_to_theme(parse_ltl_string("G(z -> F k)")))
        self.assertEqual(a, b)

    def test_too_many_literals_returns_none(self):
        node = parse_ltl_string("(d & e) | (h & i) | j")
        self.assertIsNone(ctx.remap_to_theme(node))

    def test_remapped_formula_translates(self):
        node = parse_ltl_string("G(z -> F k)")
        remapped = ctx.remap_to_theme(node)
        result = ctx.translate(remapped)
        self.assertIn("light", result.lower())
        self.assertNotIn("'z'", result)
        self.assertNotIn("'k'", result)


class TestCustomTheme(unittest.TestCase):
    """Verify that custom themes work correctly."""

    def test_custom_theme(self):
        elevator = ctx.Theme(
            name="Elevator",
            description="An elevator system",
            literals={
                "d": ("the door is open",       "the door is closed"),
                "m": ("the elevator is moving",  "the elevator is stopped"),
            },
        )

        # Safety: door must never be open while moving
        node = parse_ltl_string("G(m -> !d)")
        result = ctx.translate(node, elevator)
        self.assertIn("elevator", result.lower())
        self.assertIn("door", result.lower())

        # Response: whenever the door is open, elevator must eventually move
        node = parse_ltl_string("G(d -> F m)")
        result = ctx.translate(node, elevator)
        self.assertIn("door is open", result.lower())
        self.assertIn("elevator", result.lower())
        self.assertIn("eventually", result.lower())


if __name__ == "__main__":
    unittest.main()
