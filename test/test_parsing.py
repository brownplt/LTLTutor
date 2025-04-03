import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ltlnode import *


## LTL String --> AST Node
class TestParseLTLString(unittest.TestCase):
    def test_parse_ltl_string(self):
        test_cases = [
            ("a", LiteralNode),
            ("(abc)", LiteralNode),
            ("a & b", AndNode),
            ("a | b", OrNode),
            ("a & b", AndNode),
            ("a | b", OrNode),
            ("!a", NotNode),
            ("a -> b", ImpliesNode),
            ("a <-> b", EquivalenceNode),
            ("X(a)", NextNode),
            ("F(a)", FinallyNode),
            ("G(a)", GloballyNode),
            ("X (a & b)", NextNode),
            ("(X a) & b", AndNode),
            ("(X a) | b", OrNode),
            ("G((X a) | b)", GloballyNode),
            ("a U b", UntilNode),
            ("a & (b | c)", AndNode),
            ("(a & b) | c", OrNode)
        ]

        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


"""
Tests for the correspondence between Forge and Classic LTL syntax.
"""
class TestForgeClassicSyntaxCorrespondence(unittest.TestCase):
    def test_parse_ltl_string(self):
        test_cases = [
            # Literals
            ("a", "a"),
            # Conjunction
            ("a & b", "(a & b)"),
            # Disjunction
            ("a | b", "(a | b)"),
            # Negation
            ("!a", "!a"),
            # Implication
            ("a -> b", "(a -> b)"),
            # Equivalence
            ("a <-> b", "(a <-> b)"),
            # Next
            ("NEXT_STATE a", "(X a)"),
            # Eventually
            ("EVENTUALLY a", "(F a)"),
            # Globally
            ("ALWAYS a", "(G a)"),
            # Until
            ("a UNTIL b", "(a U b)"),
        ]

        for forge, classic in test_cases:
            with self.subTest(input=forge, expected=classic):
                self.assertEqual(str(parse_ltl_string(forge)), str(parse_ltl_string(classic)))

"""
Tests for the correspondence between Electrum and Classic LTL syntax.
"""
class TestElectrumClassicSyntaxCorrespondence(unittest.TestCase):
    def test_parse_ltl_string(self):
        test_cases = [
            # Literals
            ("a", "a"),
            # Conjunction
            ("a & b", "(a & b)"),
            # Disjunction
            ("a | b", "(a | b)"),
            # Negation
            ("!a", "!a"),
            # Implication
            ("a -> b", "(a -> b)"),
            # Equivalence
            ("a <-> b", "(a <-> b)"),
            # Next
            ("AFTER a", "(X a)"),
            # Eventually
            ("EVENTUALLY a", "(F a)"),
            # Globally
            ("ALWAYS a", "(G a)"),
            # Until
            ("a UNTIL b", "(a U b)"),
        ]

        for forge, classic in test_cases:
            with self.subTest(input=forge, expected=classic):
                self.assertEqual(str(parse_ltl_string(forge)), str(parse_ltl_string(classic)))



if __name__ == "__main__":
    unittest.main()
