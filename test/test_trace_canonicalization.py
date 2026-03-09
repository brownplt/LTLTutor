import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error in transitive imports
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()
sys.modules['inflect'] = MagicMock()
sys.modules['wordfreq'] = MagicMock(zipf_frequency=lambda *args, **kwargs: 0)

from exerciseprocessor import canonicalizeSpotTrace


class TestTraceCanonicalization(unittest.TestCase):
    def test_orders_literals_lexicographically_per_state(self):
        trace = "b & !a; c & a; cycle{!c & b; a & !b}"
        expected = "!a & b;a & c;cycle{b & !c;a & !b}"
        self.assertEqual(canonicalizeSpotTrace(trace), expected)

    def test_handles_parentheses_and_whitespace(self):
        trace = " ( b ) & ( !a ) ; cycle{ (d) & c } "
        expected = "!a & b;cycle{c & d}"
        self.assertEqual(canonicalizeSpotTrace(trace), expected)

    def test_empty_trace(self):
        self.assertEqual(canonicalizeSpotTrace("   "), "")


if __name__ == "__main__":
    unittest.main()
