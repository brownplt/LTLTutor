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
        self.assertEqual(english, "not 'p'")
    
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
        # Should be proper English
        self.assertTrue(
            "if 'p', then 'q'" == english or
            "'p' implies 'q'" == english or
            "whenever 'p', then 'q'" == english
        )
    
    def test_and_operator(self):
        """And operator should use 'both ... and'"""
        node = parse_ltl_string("p & q")
        english = node.__to_english__()
        self.assertIn("both", english)
        self.assertIn("and", english)
    
    def test_or_operator(self):
        """Or operator should use 'either ... or'"""
        node = parse_ltl_string("p | q")
        english = node.__to_english__()
        self.assertIn("either", english)
        self.assertIn("or", english)
    
    def test_until_operator(self):
        """Until operator should be clean"""
        node = parse_ltl_string("p U q")
        english = node.__to_english__()
        self.assertEqual(english, "'p' until 'q'")
    
    def test_response_pattern(self):
        """G(p -> F q) should be natural"""
        node = parse_ltl_string("G (p -> F q)")
        english = node.__to_english__()
        # Should be clean without redundant 'holds'
        self.assertNotIn("holds", english)
        self.assertIn("whenever", english)
        self.assertIn("eventually", english)
    
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
        self.assertIn("eventually", english)
        self.assertTrue(
            "simultaneously" in english or
            "same time" in english or
            "both" in english
        )
    
    def test_finally_globally_pattern(self):
        """F(G p) should be natural"""
        node = parse_ltl_string("F (G p)")
        english = node.__to_english__()
        self.assertIn("eventually", english)
        self.assertIn("always", english)
    
    def test_nested_until(self):
        """(p U q) U r should be clear"""
        node = parse_ltl_string("(p U q) U r")
        english = node.__to_english__()
        # Should mention both until relationships
        self.assertEqual(english.count("until"), 2)
    
    def test_no_double_periods(self):
        """Translations should not have double periods"""
        formulas = [
            "G p", "F p", "X p", "p U q", "p & q", "p | q",
            "G (p -> F q)", "G (F p)", "!(F p)"
        ]
        for formula in formulas:
            node = parse_ltl_string(formula)
            english = node.__to_english__()
            # Should not have .. or ...
            self.assertNotIn("..", english, f"Formula {formula} has double periods")


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


if __name__ == "__main__":
    unittest.main()
