import unittest
import sys
import os
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))
sys.modules['spot'] = MagicMock()

from exerciseprocessor import normalizeSpotTraceSyntax


class TestTraceBuilderNormalization(unittest.TestCase):
    def test_normalizes_cycle_shorthand(self):
        trace = "a; !b; {a & b; !a}"
        self.assertEqual(normalizeSpotTraceSyntax(trace), "a;!b;cycle{a & b; !a}")

    def test_normalizes_bare_cycle(self):
        self.assertEqual(normalizeSpotTraceSyntax("{a}"), "cycle{a}")

    def test_trims_and_compacts_semicolons(self):
        self.assertEqual(normalizeSpotTraceSyntax(" a ;  b ;  c "), "a;b;c")


if __name__ == '__main__':
    unittest.main()
