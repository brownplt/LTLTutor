import unittest
import sys
import os


# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import parse_ltl_string
import codebook


"""
Test cases for the conceptual mutation operators in the LTL misconceptions codebook.
"""
class TestConceptualMutator(unittest.TestCase):
    
    def apply_and_check_misconception(self, code, test_cases):
        """
        Helper function to test multiple input/output pairs for a given misconception code.
        """
        for input, expected in test_cases:
            with self.subTest(input=input, code=code):
                ast = parse_ltl_string(input)
                result = str(codebook.applyMisconception(ast, code).node)
                self.assertEqual(result, expected)

    def test_precedence(self):
        test_cases = [
            ("(a & (b | c))", "((a & b) | c)"),
            ("a & (b | c)", "((a & b) | c)"),
            ("a | (b & c)", "((a | b) & c)"),
            ("(a U d) & (b | (c <-> d))", "(((a U d) & b) | (c <-> d))"),
            ("(a -> d) & (b | (c U d))", "(((a -> d) & b) | (c U d))"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.Precedence, test_cases
        )

    def test_bad_state_index(self):
        test_cases = [
            ("(l U (q & (F s)))", "((l U q) & (F s))"),
            ("(l U (q & (G s)))", "((l U q) & (G s))"),
            ("(l U (q | (F s)))", "((l U q) | (F s))"),
            ("(l U (q | (G s)))", "((l U q) | (G s))"),
            ("(l U (q -> (F s)))", "((l U q) -> (F s))"),
            ("(l U (q -> (G s)))", "((l U q) -> (G s))"),
            ("((X (l & r)))", "((X l) & r)"),
            ("(X (X (l & r)))", "(X (l & r))"),
            ("(X (X (X (l & r))))", "(X (l & r))"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.BadStateIndex, test_cases
        )

    def test_bad_state_quantification(self):
        test_cases = [
            ("G(a -> b)", "(F (a -> b))"),
            ("F(a U b)", "(G (a U b))"),
            ("F(a)", "(G a)"),
            ("G(F(a))", "(F (F a))"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.BadStateQuantification, test_cases
        )

        random_result_cases = [
            (
                "a U b",
                [
                    "((F a) U b)",
                    "((G a) U b)",
                    "(a U (F b))",
                    "(a U (G b))",
                    "(b U a)",
                ],
            ),
            (
                "a U (F b)",
                [
                    "((F a) U (F b))",
                    "((G a) U (F b))",
                    "(a U (F (F b)))",
                    "(a U (G (F b)))",
                    "((F b) U a)",
                ],
            ),
        ]

        # Loop over random cases and run them multiple times
        for input, expected_outputs in random_result_cases:
            for i in range(10):  # Run each test 10 times
                with self.subTest(input=input, iteration=i):
                    ast = parse_ltl_string(input)
                    result = str(
                        codebook.applyMisconception(
                            ast, codebook.MisconceptionCode.BadStateQuantification
                        ).node
                    )
                    self.assertIn(result, expected_outputs)

    def test_exclusive_u(self):
        test_cases = [
            ("(x U ((! x) & y))", "(x U y)"),
            ("(x U ((! x) & (y -> z)))", "(x U (y -> z))"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.ExclusiveU, test_cases
        )

    def test_implicit_f(self):
        test_cases = [
            ("F a", "a"),
            ("F(G(b))", "(G b)"),
            ("(F(a U b))", "(a U b)"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.ImplicitF, test_cases
        )

    def test_implicit_g(self):
        test_cases = [
            ("G a", "a"),
            ("G(G(b))", "(G b)"),
            ("(G(a U b))", "(a U b)"),
        ]
        self.apply_and_check_misconception(
            codebook.MisconceptionCode.ImplicitG, test_cases
        )

    def test_weak_u(self):
        test_cases = [
            ("a U b", "((a U b) & (F b))"),
            ("a U (G b)", "((a U (G b)) & (F (G b)))"),
            ("a U (b -> c)", "((a U (b -> c)) & (F (b -> c)))"),
        ]
        self.apply_and_check_misconception(codebook.MisconceptionCode.WeakU, test_cases)


if __name__ == "__main__":
    unittest.main()
