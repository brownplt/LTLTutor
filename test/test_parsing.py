import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ltlnode import *


## LTL String --> AST Node
class TestParseLTLString(unittest.TestCase):
    def test_single_char_literal(self):
        input_str = "a"
        expected_node = LiteralNode
        self.assertIsInstance(parse_ltl_string(input_str), expected_node)

    def test_parenthesized_literal(self):
        input_str = "(abc)"
        expected_node = LiteralNode
        self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_conjunctions(self):
        test_cases = [
            ("a & b", AndNode),
            ("a & (b | c)", AndNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)

    def test_disjunctions(self):
        test_cases = [
            ("a | b", OrNode),
            ("(a & b) | c", OrNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)

    def test_negations(self):
        test_cases = [
            ("!a", NotNode),
            ("! a", NotNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)

    def test_implications(self):
        test_cases = [
            ("a -> b", ImpliesNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)

    def test_equivalences(self):
        test_cases = [
            ("a <-> b", EquivalenceNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_next(self):
        test_cases = [
            ("X a", NextNode),
            ("X (a & b)", NextNode),
            ("X (a | b)", NextNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_finally(self):
        test_cases = [
            ("F a", FinallyNode),
            ("F (a & b)", FinallyNode),
            ("F (a | b)", FinallyNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_globally(self):
        test_cases = [
            ("G a", GloballyNode),
            ("G (a & b)", GloballyNode),
            ("G (a | b)", GloballyNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_until(self):
        test_cases = [
            ("a U b", UntilNode),
            ("a U (b & c)", UntilNode),
            ("(a & b) U c", UntilNode),
        ]
        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)


    def test_complex_formulas(self):
        test_cases = [
            ("X (a & b)", NextNode),
            ("(X a) & b", AndNode),
            ("(X a) | b", OrNode),
            ("G((X a) | b)", GloballyNode),
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
