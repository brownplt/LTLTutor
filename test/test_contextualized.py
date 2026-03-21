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
    ("G r",                   "Invariant"),
    ("F r",                   "Liveness"),
    ("G !r",                  "Safety / never"),
    ("G (r -> F g)",          "Response"),
    ("G (r -> X g)",          "Immediate response"),
    ("G(r -> (F g & F b))",   "Chain response"),
    ("G(r -> (g U b))",       "Chain precedence"),
    ("F (G r)",               "Persistence"),
    ("G (F r)",               "Recurrence"),
    ("(G r) U (F g)",         "Obligation until release"),
    ("G(r -> X r)",           "Once true, stays true"),
    ("!(F r)",                "Impossibility"),
    ("r -> g",                "Simple implication"),
    ("G(r -> X(F g))",        "Bounded response"),
    ("F(G(r -> F g))",        "Eventual stable response"),
    ("G((r U g) -> F b)",     "Until-triggered response"),
    ("!(r & g)",              "Mutual exclusion"),
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
        result = self._tr("G r")
        self.assertIn("red light", result.lower())
        self.assertIn("all times", result.lower())

    def test_finally_literal(self):
        result = self._tr("F r")
        self.assertIn("red light", result.lower())
        self.assertIn("eventually", result.lower())

    def test_never(self):
        result = self._tr("G !r")
        self.assertIn("red light", result.lower())
        self.assertIn("never", result.lower())

    def test_response_uses_event_form(self):
        """G(r -> F g) should use 'turns on' not just 'is on'."""
        result = self._tr("G(r -> F g)")
        self.assertIn("red light turns on", result.lower())
        self.assertIn("green light", result.lower())
        self.assertIn("eventually", result.lower())

    def test_immediate_response(self):
        result = self._tr("G(r -> X g)")
        self.assertIn("red light turns on", result.lower())
        self.assertIn("green light", result.lower())
        self.assertIn("next step", result.lower())

    def test_chain_response_mentions_both(self):
        result = self._tr("G(r -> (F g & F b))")
        self.assertIn("red light", result.lower())
        self.assertIn("green light", result.lower())
        self.assertIn("blue light", result.lower())

    def test_persistence(self):
        result = self._tr("G(r -> X r)")
        self.assertIn("red light", result.lower())
        self.assertIn("forever", result.lower())

    def test_recurrence(self):
        result = self._tr("G(F r)")
        self.assertIn("red light", result.lower())
        self.assertIn("over and over", result.lower())

    def test_mutual_exclusion(self):
        result = self._tr("!(r & g)")
        self.assertIn("red light", result.lower())
        self.assertIn("green light", result.lower())

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
            for lit in ["'r'", "'g'", "'b'"]:
                self.assertNotIn(lit, result,
                                 f"{formula_str} => still has abstract literal {lit}: {result}")


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
            event_form={
                "d": ("the door opens",           "the door closes"),
                "m": ("the elevator starts moving", "the elevator stops"),
            },
        )

        # Safety: door must never be open while moving
        node = parse_ltl_string("G(m -> !d)")
        result = ctx.translate(node, elevator)
        self.assertIn("elevator", result.lower())
        self.assertIn("door", result.lower())

        # Response: if door opens, elevator must eventually move
        node = parse_ltl_string("G(d -> F m)")
        result = ctx.translate(node, elevator)
        self.assertIn("door opens", result.lower())
        self.assertIn("elevator", result.lower())
        self.assertIn("eventually", result.lower())


if __name__ == "__main__":
    unittest.main()
