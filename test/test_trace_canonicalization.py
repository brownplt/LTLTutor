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

from exerciseprocessor import canonicalizeSpotTrace, NodeRepr


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

    def test_unicode_negation_does_not_affect_order(self):
        trace = "b & ¬a & c; cycle{¬b & a}"
        expected = "!a & b & c;cycle{a & !b}"
        self.assertEqual(canonicalizeSpotTrace(trace), expected)

    def test_bang_negation_does_not_affect_lexicographic_order(self):
        trace = "!z & a & !b & c"
        expected = "a & !b & c & !z"
        self.assertEqual(canonicalizeSpotTrace(trace), expected)

    def test_display_label_still_shows_negation_symbol(self):
        from exerciseprocessor import _nodeReprDisplayLabel
        node = NodeRepr("!b & a")
        rendered = _nodeReprDisplayLabel(node)
        self.assertIn("¬b", rendered)

    def test_canonicalize_resolves_or_in_state(self):
        """SPOT may output states with | (OR). canonicalizeSpotTrace must resolve
        ORs before reordering literals, otherwise the trace gets corrupted."""
        trace = "(s & v) | (!s & !v); cycle{1}"
        result = canonicalizeSpotTrace(trace)
        # The OR should be resolved to one concrete branch, not garbled
        self.assertNotIn("|", result.split("cycle")[0],
            "OR should be resolved in prefix states")
        # Result must be one of the two valid branches
        prefix = result.split(";")[0].strip()
        self.assertIn(prefix, ["s & v", "!s & !v"],
            f"Expected a valid branch, got '{prefix}'")

    def test_canonicalize_resolves_or_in_cycle(self):
        """ORs in cycle states must also be resolved."""
        trace = "s & v; cycle{(s & v) | (!s & !v)}"
        result = canonicalizeSpotTrace(trace)
        # Extract cycle content
        cycle_part = result.split("cycle{")[1].rstrip("}")
        self.assertNotIn("|", cycle_part,
            "OR should be resolved in cycle states")
        self.assertIn(cycle_part, ["s & v", "!s & !v"],
            f"Expected a valid branch in cycle, got '{cycle_part}'")

    def test_canonicalize_preserves_simple_traces(self):
        """Traces without OR should be unaffected by the OR-resolution step."""
        trace = "!s & v; cycle{s & !v}"
        result = canonicalizeSpotTrace(trace)
        self.assertEqual(result, "!s & v;cycle{s & !v}")


if __name__ == "__main__":
    unittest.main()
