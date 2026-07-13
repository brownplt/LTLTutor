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

from exerciseprocessor import getFormulaLiterals, expandSpotTrace, traceToRenderData


class TestGetFormulaLiterals(unittest.TestCase):
    """Regression tests for the bug where getFormulaLiterals used exact
    `type(n) is ...` checks against the operator base classes. Real formulas are
    built from subclasses (AndNode, GloballyNode, UntilNode, ...), so the walk
    never recursed and every non-trivial formula returned an empty set. That
    empty set made expandSpotTrace a no-op, leaving raw spot "1" tautology states
    and partial states in the rendered traces."""

    def test_recurses_through_temporal_and_boolean_operators(self):
        self.assertEqual(getFormulaLiterals("G(d -> F e)"), {"d", "e"})
        self.assertEqual(getFormulaLiterals("F(d & e)"), {"d", "e"})
        self.assertEqual(getFormulaLiterals("d U e"), {"d", "e"})
        self.assertEqual(getFormulaLiterals("X d"), {"d"})

    def test_single_literal(self):
        self.assertEqual(getFormulaLiterals("a"), {"a"})

    def test_boolean_constants_are_not_literals(self):
        self.assertEqual(getFormulaLiterals("true"), set())
        self.assertEqual(getFormulaLiterals("false"), set())
        self.assertEqual(getFormulaLiterals("(a & true) | false"), {"a"})


class TestExpansionFillsEveryState(unittest.TestCase):
    """With a correct literal set, every trace state must become a full valuation:
    no bare "1" tautology states and no state missing a variable."""

    def _labels(self, render_data):
        return ([s["label"] for s in render_data["prefix"]]
                + [s["label"] for s in render_data["cycle"]])

    def test_tautology_and_partial_states_get_expanded(self):
        # Mirrors the reported trace: "1; d & e; !e; cycle{1; 1}".
        trace = "1; d & e; !e; cycle{1; 1}"
        expanded = expandSpotTrace(trace, literals=["d", "e"])
        labels = self._labels(traceToRenderData(expanded))

        self.assertTrue(labels, "expected rendered states")
        for label in labels:
            self.assertNotIn("1", label, f"tautology state left unexpanded: {label!r}")
            # Every state mentions both variables (¬ is the display negation).
            self.assertIn("d", label, f"state missing d: {label!r}")
            self.assertIn("e", label, f"state missing e: {label!r}")

    def test_empty_literals_leaves_trace_unexpanded(self):
        # Guards the interaction that caused the bug: no literals => no expansion,
        # so the tautology state survives. This is why the literal set must be
        # populated by getFormulaLiterals upstream.
        trace = "1; d & e; cycle{1}"
        expanded = expandSpotTrace(trace, literals=[])
        labels = self._labels(traceToRenderData(expanded))
        self.assertIn("1", labels)


if __name__ == "__main__":
    unittest.main()
