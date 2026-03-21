"""Side-by-side comparison of three LTL-to-English translation approaches.

Run with:
    python -m pytest test/test_translation_comparison.py -v -s

The -s flag is important to see the printed comparison tables.
"""

import unittest
import sys
import os
import random

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import parse_ltl_string
import ltltoeng
import ltltoeng_structured as structured
import ltltoeng_prose as prose


# ---------------------------------------------------------------------------
# Test formulas grouped by category
# ---------------------------------------------------------------------------

SIMPLE_FORMULAS = [
    ("G p",         "Globally literal"),
    ("F p",         "Finally literal"),
    ("X p",         "Next literal"),
    ("p U q",       "Until"),
    ("p & q",       "And"),
    ("p | q",       "Or"),
    ("p -> q",      "Implies"),
    ("!p",          "Not"),
]

RESPONSE_PATTERNS = [
    ("G (p -> F q)",      "Response pattern"),
    ("G (p -> X q)",      "Immediate response"),
    ("G (p -> X(F q))",   "Bounded response"),
    ("G(p -> (F q & F r))", "Chain response"),
    ("G(p -> (q U r))",   "Chain precedence"),
]

RECURRENCE_PERSISTENCE = [
    ("G (F p)",           "Recurrence (infinitely often)"),
    ("F (G p)",           "Persistence (stability)"),
    ("G !p",              "Never"),
    ("!(F p)",            "Never (negated finally)"),
]

COMPLEX_NESTED = [
    ("F(G(p -> F q))",    "Eventual stable response"),
    ("G((p U q) -> F r)", "Until-triggered response"),
    ("(G p) U (F q)",     "Globally until finally"),
    ("(p U q) U r",       "Nested until"),
    ("G(p -> X p)",       "Final state (persistence)"),
]

NEXT_CHAINS = [
    ("X X X p",           "Triple next"),
    ("(X p) -> (X X X q)", "Aligned next implication"),
]

PROPOSITIONAL = [
    ("!!p",               "Double negation"),
    ("!(p & q)",          "Negated conjunction (De Morgan)"),
    ("!(p | q)",          "Negated disjunction (De Morgan)"),
    ("!(p -> q)",         "Negated implication"),
    ("!p & !q",           "And of negations"),
    ("!p | !q",           "Or of negations"),
    ("(p & q) -> r",      "Conjunction implies"),
    ("p -> (q & r)",      "Implies conjunction"),
    ("!p -> q",           "Negation implies (unless)"),
]

ALL_FORMULAS = (
    SIMPLE_FORMULAS
    + RESPONSE_PATTERNS
    + RECURRENCE_PERSISTENCE
    + COMPLEX_NESTED
    + NEXT_CHAINS
    + PROPOSITIONAL
)


# ---------------------------------------------------------------------------
# Helper: translate with all three systems
# ---------------------------------------------------------------------------

def _translate_all(formula_str: str):
    """Return (original, structured, prose) translations."""
    random.seed(42)  # deterministic for original translator
    node = parse_ltl_string(formula_str)

    original = ltltoeng.finalize_sentence(node.__to_english__())
    struct = structured.translate(parse_ltl_string(formula_str))
    pro = prose.translate(parse_ltl_string(formula_str))

    return original, struct, pro


# ---------------------------------------------------------------------------
# Comparison printer (runs as a test so it shows up with -s)
# ---------------------------------------------------------------------------

class TestTranslationComparison(unittest.TestCase):
    """Print side-by-side translations for manual review."""

    def setUp(self):
        random.seed(42)

    def test_print_comparison_table(self):
        """Print all translations for visual comparison."""
        print("\n" + "=" * 100)
        print("LTL-TO-ENGLISH TRANSLATION COMPARISON")
        print("=" * 100)

        categories = [
            ("SIMPLE", SIMPLE_FORMULAS),
            ("RESPONSE PATTERNS", RESPONSE_PATTERNS),
            ("RECURRENCE / PERSISTENCE", RECURRENCE_PERSISTENCE),
            ("COMPLEX NESTED", COMPLEX_NESTED),
            ("NEXT CHAINS", NEXT_CHAINS),
            ("PROPOSITIONAL", PROPOSITIONAL),
        ]

        for cat_name, formulas in categories:
            print(f"\n{'─' * 100}")
            print(f"  {cat_name}")
            print(f"{'─' * 100}")

            for formula_str, description in formulas:
                original, struct, pro = _translate_all(formula_str)

                print(f"\n  Formula:    {formula_str}  ({description})")
                print(f"  Original:   {original}")

                # For structured output, indent multi-line
                if "\n" in struct:
                    lines = struct.split("\n")
                    print(f"  Structured: {lines[0]}")
                    for line in lines[1:]:
                        print(f"              {line}")
                else:
                    print(f"  Structured: {struct}")

                # For prose output, show multi-sentence flow
                print(f"  Prose:      {pro}")

        print("\n" + "=" * 100)


# ---------------------------------------------------------------------------
# Actual assertions
# ---------------------------------------------------------------------------

class TestStructuredBasicProperties(unittest.TestCase):
    """Basic assertions for the structured translator."""

    def setUp(self):
        random.seed(42)

    def test_simple_formulas_are_single_line(self):
        """Simple formulas should not produce bullet points."""
        for formula_str, _ in SIMPLE_FORMULAS:
            node = parse_ltl_string(formula_str)
            result = structured.translate(node)
            self.assertNotIn("\n", result,
                             f"Simple formula {formula_str} should be single-line, got:\n{result}")

    def test_complex_formulas_use_bullets(self):
        """Complex formulas should produce multi-line output with bullets."""
        complex_formulas = [
            "F(G(p -> F q))",
            "G(p -> (F q & F r))",
            "G(p -> X(F q))",
        ]
        for formula_str in complex_formulas:
            node = parse_ltl_string(formula_str)
            result = structured.translate(node)
            self.assertIn("-", result,
                          f"Complex formula {formula_str} should have bullets, got:\n{result}")

    def test_response_pattern(self):
        node = parse_ltl_string("G(p -> F q)")
        result = structured.translate(node)
        self.assertIn("'p'", result)
        self.assertIn("'q'", result)
        self.assertIn("eventually", result.lower())

    def test_recurrence(self):
        node = parse_ltl_string("G(F p)")
        result = structured.translate(node)
        self.assertIn("infinitely often", result.lower())

    def test_persistence(self):
        node = parse_ltl_string("F(G p)")
        result = structured.translate(node)
        self.assertIn("permanently", result.lower())

    def test_never(self):
        node = parse_ltl_string("G !p")
        result = structured.translate(node)
        self.assertIn("never", result.lower())

    def test_eventual_stable_response(self):
        node = parse_ltl_string("F(G(p -> F q))")
        result = structured.translate(node)
        self.assertIn("permanent", result.lower())
        self.assertIn("'p'", result)
        self.assertIn("'q'", result)


class TestProseBasicProperties(unittest.TestCase):
    """Basic assertions for the prose translator."""

    def setUp(self):
        random.seed(42)

    def test_all_translations_end_with_period(self):
        """Every translation should end with a period."""
        for formula_str, _ in ALL_FORMULAS:
            node = parse_ltl_string(formula_str)
            result = prose.translate(node)
            self.assertTrue(result.endswith("."),
                            f"Translation of {formula_str} should end with period: {result}")

    def test_all_translations_start_capitalized_or_quoted(self):
        """Every translation should start with a capital letter or a quote."""
        for formula_str, _ in ALL_FORMULAS:
            node = parse_ltl_string(formula_str)
            result = prose.translate(node)
            self.assertTrue(
                result[0].isupper() or result[0] == "'",
                f"Translation of {formula_str} should start capitalized: {result}")

    def test_response_pattern(self):
        node = parse_ltl_string("G(p -> F q)")
        result = prose.translate(node)
        self.assertIn("whenever", result.lower())
        self.assertIn("eventually", result.lower())

    def test_recurrence(self):
        node = parse_ltl_string("G(F p)")
        result = prose.translate(node)
        self.assertIn("infinitely often", result.lower())

    def test_persistence(self):
        node = parse_ltl_string("F(G p)")
        result = prose.translate(node)
        self.assertIn("forever", result.lower())

    def test_never(self):
        node = parse_ltl_string("G !p")
        result = prose.translate(node)
        self.assertIn("never", result.lower())

    def test_multi_sentence_for_complex(self):
        """Complex formulas should produce multiple sentences."""
        node = parse_ltl_string("F(G(p -> F q))")
        result = prose.translate(node)
        # Count sentences (periods not at end)
        sentences = [s.strip() for s in result.split(".") if s.strip()]
        self.assertGreaterEqual(len(sentences), 2,
                                f"Expected multi-sentence for F(G(p->Fq)), got: {result}")

    def test_de_morgan_neither_nor(self):
        node = parse_ltl_string("!(p | q)")
        result = prose.translate(node)
        self.assertIn("neither", result.lower())
        self.assertIn("nor", result.lower())

    def test_de_morgan_not_both(self):
        node = parse_ltl_string("!(p & q)")
        result = prose.translate(node)
        self.assertIn("not both", result.lower())

    def test_persistence_same_literal(self):
        node = parse_ltl_string("G(p -> X p)")
        result = prose.translate(node)
        self.assertIn("once", result.lower())
        self.assertIn("forever", result.lower())

    def test_until_triggered_response(self):
        """G((p U q) -> F r) should mention until and eventually."""
        node = parse_ltl_string("G((p U q) -> F r)")
        result = prose.translate(node)
        self.assertIn("until", result.lower())
        self.assertIn("eventually", result.lower())

    def test_globally_until_finally(self):
        """(G p) U (F q) should produce multi-sentence."""
        node = parse_ltl_string("(G p) U (F q)")
        result = prose.translate(node)
        sentences = [s.strip() for s in result.split(".") if s.strip()]
        self.assertGreaterEqual(len(sentences), 2)


if __name__ == "__main__":
    unittest.main()
