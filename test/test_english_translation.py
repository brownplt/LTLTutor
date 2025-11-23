import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import *
import random


class TestEnglishTranslation(unittest.TestCase):
    """Test that LTL formulas are translated to natural English"""
    
    def setUp(self):
        # Seed random for consistent test results
        random.seed(42)
    
    def test_literals_no_redundant_holds(self):
        """Literals should not have redundant 'holds' in simple contexts"""
        node = parse_ltl_string("p")
        english = node.__to_english__()
        # Should be just "'p'", not "'p' holds"
        self.assertEqual(english, "'p'")
    
    def test_negation_simple(self):
        """Simple negation should be clean"""
        node = parse_ltl_string("!p")
        english = node.__to_english__()
        self.assertEqual(english, "Not 'p'")
    
    def test_globally_natural_phrasing(self):
        """Globally operator should use natural phrasing"""
        node = parse_ltl_string("G p")
        english = node.__to_english__()
        # Should not contain awkward "it is always the case that 'p' holds"
        self.assertNotIn("'p' holds", english)
        # Should be one of the natural alternatives
        self.assertIn("'p'", english)
        self.assertTrue(
            "always" in english.lower() or 
            "at all times" in english.lower()
        )
    
    def test_finally_natural_phrasing(self):
        """Finally operator should use natural phrasing"""
        node = parse_ltl_string("F p")
        english = node.__to_english__()
        # Should not have redundant holds
        self.assertNotIn("'p' holds", english)
        self.assertIn("'p'", english)
        self.assertIn("eventually", english.lower())
    
    def test_next_natural_phrasing(self):
        """Next operator should use 'step' not 'state'"""
        node = parse_ltl_string("X p")
        english = node.__to_english__()
        self.assertIn("next step", english)
        self.assertNotIn("next state", english)
    
    def test_implication_grammatically_correct(self):
        """Implication should be grammatically correct"""
        node = parse_ltl_string("p -> q")
        english = node.__to_english__()
        # Should NOT be "'q' holds is necessary for 'p' holds"
        self.assertNotIn("is necessary for", english)
        # Should be proper English (case-insensitive check)
        self.assertTrue(
            "if 'p', then 'q'" == english.lower() or
            "'p' implies 'q'" == english.lower() or
            "whenever 'p', then 'q'" == english.lower()
        )
    
    def test_and_operator(self):
        """And operator should use 'both ... and'"""
        node = parse_ltl_string("p & q")
        english = node.__to_english__()
        self.assertIn("both", english.lower())
        self.assertIn("and", english.lower())
    
    def test_or_operator(self):
        """Or operator should use 'either ... or'"""
        node = parse_ltl_string("p | q")
        english = node.__to_english__()
        self.assertIn("either", english.lower())
        self.assertIn("or", english.lower())
    
    def test_until_operator(self):
        """Until operator should be clean"""
        node = parse_ltl_string("p U q")
        english = node.__to_english__()
        # Check case-insensitive since it may be capitalized
        self.assertEqual(english.lower(), "'p' until 'q'")
    
    def test_response_pattern(self):
        """G(p -> F q) should be natural"""
        node = parse_ltl_string("G (p -> F q)")
        english = node.__to_english__()
        # Should be clean without redundant 'holds'
        self.assertNotIn("holds", english)
        self.assertIn("whenever", english.lower())
        self.assertIn("eventually", english.lower())
    
    def test_recurrence_pattern(self):
        """G(F p) should be natural"""
        node = parse_ltl_string("G (F p)")
        english = node.__to_english__()
        # Should be about happening infinitely often or always eventually
        self.assertTrue(
            "infinitely often" in english or
            "always" in english
        )
        self.assertNotIn("'p' holds", english)
    
    def test_never_pattern(self):
        """G !p should be natural"""
        node = parse_ltl_string("G !p")
        english = node.__to_english__()
        self.assertIn("never", english)
        self.assertIn("'p'", english)
    
    def test_multiple_next(self):
        """Multiple X operators should use 'steps' not 'states'"""
        node = parse_ltl_string("X X X p")
        english = node.__to_english__()
        self.assertIn("3 steps", english)
        self.assertNotIn("3 states", english)
    
    def test_not_finally_pattern(self):
        """!(F p) should be natural"""
        node = parse_ltl_string("!(F p)")
        english = node.__to_english__()
        self.assertIn("never", english)
        self.assertIn("'p'", english)
    
    def test_finally_and_pattern(self):
        """F(p & q) should mention simultaneity"""
        node = parse_ltl_string("F (p & q)")
        english = node.__to_english__()
        self.assertIn("eventually", english.lower())
        self.assertTrue(
            "simultaneously" in english.lower() or
            "same time" in english.lower() or
            "both" in english.lower()
        )
    
    def test_finally_globally_pattern(self):
        """F(G p) should be natural"""
        node = parse_ltl_string("F (G p)")
        english = node.__to_english__()
        self.assertIn("eventually", english.lower())
        self.assertIn("always", english.lower())
    
    def test_nested_until(self):
        """(p U q) U r should be clear"""
        node = parse_ltl_string("(p U q) U r")
        english = node.__to_english__()
        # Should mention both until relationships
        self.assertEqual(english.count("until"), 2)
    
    def test_no_double_periods(self):
        """Translations should not have consecutive periods (e.g., '..', '...')"""
        formulas = [
            "G p", "F p", "X p", "p U q", "p & q", "p | q",
            "G (p -> F q)", "G (F p)", "!(F p)"
        ]
        for formula in formulas:
            node = parse_ltl_string(formula)
            english = node.__to_english__()
            # Should not have consecutive periods
            self.assertNotIn("..", english, f"Formula {formula} has consecutive periods")


class TestEquivalenceTranslation(unittest.TestCase):
    """Test equivalence operator translations"""
    
    def setUp(self):
        random.seed(42)
    
    def test_equivalence_natural(self):
        """Equivalence should be natural"""
        node = parse_ltl_string("p <-> q")
        english = node.__to_english__()
        self.assertTrue(
            "if and only if" in english or
            "equivalent to" in english or
            "exactly when" in english
        )


class TestContextAwareTranslations(unittest.TestCase):
    """Test context-aware translations that address deictic shift issues"""
    
    def setUp(self):
        random.seed(42)
    
    def test_globally_finally_and_simultaneity(self):
        """G(F(p & q)) should make simultaneity context clear"""
        node = parse_ltl_string("G(F(p & q))")
        english = node.__to_english__()
        # Should mention both temporal context and simultaneity
        self.assertIn("at all times", english.lower())
        self.assertIn("eventually", english.lower())
        self.assertIn("simultaneously", english.lower())
    
    def test_finally_globally_implies_finally_context(self):
        """F(G(p -> F q)) should clarify nested temporal references"""
        node = parse_ltl_string("F(G(p -> F q))")
        english = node.__to_english__()
        # Should establish clear temporal context
        self.assertIn("eventually", english.lower())
        self.assertIn("from then on", english.lower())
        self.assertIn("whenever", english.lower())
    
    def test_globally_until_finally_context(self):
        """(G p) U (F q) should clarify the until relationship"""
        node = parse_ltl_string("(G p) U (F q)")
        english = node.__to_english__()
        # Should clarify that globally p continues until eventually q
        self.assertIn("at all times", english.lower())
        self.assertIn("until", english.lower())
        self.assertIn("eventually", english.lower())
    
    def test_next_until_context(self):
        """X(p U q) should clarify the next step context"""
        node = parse_ltl_string("X(p U q)")
        english = node.__to_english__()
        # Should mention next step and the until relationship
        self.assertIn("next step", english.lower())
        self.assertIn("until", english.lower())
    
    def test_globally_until_implies_finally_context(self):
        """G((p U q) -> F r) should handle the implication properly"""
        node = parse_ltl_string("G((p U q) -> F r)")
        english = node.__to_english__()
        # Should mention whenever, until, and eventually
        self.assertIn("whenever", english.lower())
        self.assertIn("until", english.lower())
        self.assertIn("eventually", english.lower())
    
    def test_nested_until_clarity(self):
        """(p U q) U r should clarify nested until relationships"""
        node = parse_ltl_string("(p U q) U r")
        english = node.__to_english__()
        # Should have two mentions of "until"
        self.assertEqual(english.lower().count("until"), 2)
        self.assertIn("continues", english.lower())


class TestFinalStatePatterns(unittest.TestCase):
    """Test final state patterns where a proposition becomes permanently true"""
    
    def setUp(self):
        random.seed(42)
    
    def test_final_state_next_pattern(self):
        """G(p -> X p) should translate to 'once p, it will always hold'"""
        node = parse_ltl_string("G(p -> X p)")
        english = node.__to_english__()
        self.assertIn("once", english.lower())
        self.assertIn("always hold", english.lower())
        self.assertIn("'p'", english)
    
    def test_final_state_globally_pattern(self):
        """G(p -> G p) should translate to 'once p, it will always hold'"""
        node = parse_ltl_string("G(p -> G p)")
        english = node.__to_english__()
        self.assertIn("once", english.lower())
        self.assertIn("always hold", english.lower())
        self.assertIn("'p'", english)
    
    def test_final_state_different_literals_next(self):
        """G(p -> X q) should not match final state pattern"""
        node = parse_ltl_string("G(p -> X q)")
        english = node.__to_english__()
        # Should not use "once" phrasing since literals differ
        self.assertNotIn("once", english.lower())
    
    def test_final_state_different_literals_globally(self):
        """G(p -> G q) should not match final state pattern"""
        node = parse_ltl_string("G(p -> G q)")
        english = node.__to_english__()
        # Should not use "once" phrasing since literals differ
        self.assertNotIn("once", english.lower())


class TestCapitalization(unittest.TestCase):
    """Test that English translations follow proper capitalization conventions"""
    
    def setUp(self):
        random.seed(42)
    
    def test_sentences_start_with_capital(self):
        """Most sentences should start with a capital letter"""
        formulas = [
            "G p",
            "F p", 
            "X p",
            "p & q",
            "p | q",
            "!p",
            "G (p -> F q)",
            "G(F(p & q))",
            "F(G p)"
        ]
        for formula in formulas:
            with self.subTest(formula=formula):
                node = parse_ltl_string(formula)
                english = node.__to_english__()
                # Should start with capital letter (unless it starts with a quote)
                if english and not english.startswith("'"):
                    self.assertTrue(
                        english[0].isupper(),
                        f"'{english}' should start with a capital letter"
                    )
    
    def test_literals_not_capitalized_when_quoted(self):
        """Literals in quotes at the start should not be capitalized"""
        # When a translation naturally starts with a quoted literal,
        # the quote should remain as-is
        node = parse_ltl_string("p")
        english = node.__to_english__()
        self.assertEqual(english, "'p'")  # Should not become "'P'"


if __name__ == "__main__":
    unittest.main()
