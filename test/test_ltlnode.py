import unittest
from ltlnode import *

class TestParseLTLString(unittest.TestCase):
    def test_parse_ltl_string(self):
        test_cases = [
            ('a', LiteralNode),
            ('(abc)', LiteralNode),
            ('a && b', AndNode),
            ('a || b', OrNode),
            ('!a', NotNode),
            ('a => b', ImpliesNode),
            ('a <=> b', EquivalenceNode),
            ('X(a)', NextNode),
            ('F(a)', FinallyNode),
            ('G(a)', GloballyNode),
            ('X a && b', NextNode),
            ('(X a) && b', AndNode),
            ('a U b', UntilNode)
        ]

        for input_str, expected_node in test_cases:
            with self.subTest(input=input_str, expected=expected_node):
                self.assertIsInstance(parse_ltl_string(input_str), expected_node)

if __name__ == '__main__':
    unittest.main()