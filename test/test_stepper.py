"""Tests for stepper.py -- the per-step trace-satisfaction view shown to students.

The stepper walks an LTL formula's syntax tree against a (lasso-shaped) trace
and marks, for every subformula at every time step, whether it holds. This drives
the coloured formula tree and the satisfaction matrix a student sees when they
step through a trace. It was previously at 0% coverage.

Uses the real SPOT kernel (satisfaction values come from spotutils). Skipped
cleanly when SPOT is unavailable.
"""

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import realspot

_loaded = realspot.load_real("spotutils", "stepper")
SPOT_AVAILABLE = _loaded is not None
if SPOT_AVAILABLE:
    spotutils, stepper = _loaded
    parse = stepper.parse_ltl_string


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestSplitTraceAtCycle(unittest.TestCase):
    def test_prefix_and_cycle(self):
        self.assertEqual(stepper.splitTraceAtCycle("a; b; cycle{c}"), (["a", "b"], ["c"]))

    def test_cycle_only(self):
        self.assertEqual(stepper.splitTraceAtCycle("cycle{a}"), ([], ["a"]))

    def test_no_cycle(self):
        self.assertEqual(stepper.splitTraceAtCycle("a; b"), (["a", "b"], []))

    def test_multiliteral_states_preserved(self):
        prefix, cycle = stepper.splitTraceAtCycle("! a; cycle{a & b}")
        self.assertEqual(prefix, ["! a"])
        self.assertEqual(cycle, ["a & b"])


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestTraceSatisfactionPerStep(unittest.TestCase):
    def test_empty_trace_returns_empty_list(self):
        self.assertEqual(stepper.traceSatisfactionPerStep(parse("G a"), "", "Classic"), [])

    def test_state_counts_match_trace_shape(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; b; cycle{a}", "Classic")
        prefix, cycle = stepper.splitTraceAtCycle("! a; b; cycle{a}")
        self.assertEqual(len(result.prefix_states), len(prefix))
        self.assertEqual(len(result.cycle_states), len(cycle))

    def test_globally_satisfaction_per_state(self):
        # G a on  !a ; cycle{a}:  fails at step 0 (a is false there),
        # but from step 1 onward a holds forever, so G a holds in the cycle.
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; cycle{a}", "Classic")
        self.assertFalse(result.prefix_states[0].satisfied)
        self.assertTrue(result.cycle_states[0].satisfied)

    def test_eventually_never_satisfied_when_atom_absent(self):
        # F a on cycle{!a}: a never occurs, so F a is false at every state.
        result = stepper.traceSatisfactionPerStep(parse("F a"), "cycle{! a}", "Classic")
        for state in result.prefix_states + result.cycle_states:
            self.assertFalse(state.satisfied)

    def test_root_satisfaction_agrees_with_spotutils(self):
        # Cross-check: the root node's satisfaction at the first state must equal
        # an independent is_trace_satisfied() call on the whole trace. This ties
        # the stepper's recursive walk back to the SPOT ground truth.
        cases = [
            ("G a", "! a; cycle{a}"),
            ("F a", "! a; ! a; cycle{a}"),
            ("a U b", "a & ! b; cycle{b}"),
            ("X a", "! a; cycle{a}"),
        ]
        for formula, trace in cases:
            result = stepper.traceSatisfactionPerStep(parse(formula), trace, "Classic")
            expected = spotutils.is_trace_satisfied(trace=trace, formula=formula)
            self.assertEqual(
                result.prefix_states[0].satisfied, expected,
                f"stepper disagrees with spotutils for {formula!r} on {trace!r}",
            )

    def test_subformula_satisfaction_matches_spotutils_at_first_state(self):
        # Every subformula's truth at the first state should match evaluating
        # that subformula directly against the trace.
        trace = "! a; cycle{a & b}"
        result = stepper.traceSatisfactionPerStep(parse("G (a & b)"), trace, "Classic")
        for subformula, satisfied in result.prefix_states[0].getAllSubformulae():
            expected = spotutils.is_trace_satisfied(trace=trace, formula=subformula)
            self.assertEqual(satisfied, expected, f"subformula {subformula!r}")


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestMatrixView(unittest.TestCase):
    def test_matrix_shape_and_binary_values(self):
        trace = "! a; cycle{a}"
        result = stepper.traceSatisfactionPerStep(parse("G a"), trace, "Classic")
        num_states = len(result.prefix_states) + len(result.cycle_states)
        view = result.getMatrixView()

        # One row per unique subformula; each row spans every time step.
        self.assertEqual(len(view["matrix"]), len(view["subformulae"]))
        for row in view["matrix"]:
            self.assertEqual(len(row), num_states)
            self.assertTrue(all(v in (0, 1) for v in row))

        # rows[] mirrors matrix[] with the subformula label attached.
        self.assertEqual([r["values"] for r in view["rows"]], view["matrix"])
        self.assertEqual([r["subformula"] for r in view["rows"]], view["subformulae"])

    def test_matrix_includes_atom_and_root(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; cycle{a}", "Classic")
        view = result.getMatrixView()
        self.assertIn("a", view["subformulae"])
        self.assertIn("(G a)", view["subformulae"])

    def test_empty_states_give_empty_matrix(self):
        empty = stepper.TraceSatisfactionResult([], [])
        self.assertEqual(empty.getMatrixView(), {"subformulae": [], "matrix": [], "rows": []})


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestRenderDataAndHtml(unittest.TestCase):
    def test_render_data_formats_negation_and_conjunction(self):
        data = stepper.getTraceRenderData("! a; cycle{a & b}")
        self.assertEqual(data["prefix"], [{"label": "¬a"}])          # ¬a
        self.assertEqual(data["cycle"], [{"label": "a   b"}])        # em-space between a and b

    def test_formula_tree_html_marks_sat_and_unsat(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; cycle{a}", "Classic")
        html = result.prefix_states[0].formulaTreeAsHTML
        self.assertIn("formula-tree", html)
        # G a is unsatisfied at state 0, its atom child also unsatisfied there.
        self.assertIn("tree-unsat", html)

    def test_getAllSubformulae_covers_whole_tree(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "cycle{a}", "Classic")
        subs = dict(result.cycle_states[0].getAllSubformulae())
        # Root 'G a' and atom 'a' both present.
        self.assertIn("(G a)", subs)
        self.assertIn("a", subs)


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestStepperViewData(unittest.TestCase):
    """The stepper renders one formula tree and re-colours it per step, so the
    truth vectors have to line up with the data-node-index values in the markup."""

    def test_one_vector_per_trace_state(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; a; cycle{a}", "Classic")
        data = result.getStepperViewData()
        self.assertEqual(len(data["steps"]), 3)

    def test_node_indices_are_preorder_and_cover_every_value(self):
        result = stepper.traceSatisfactionPerStep(parse("(G a) U b"), "! b; cycle{a & b}", "Classic")
        data = result.getStepperViewData()

        indices = [int(m) for m in re.findall(r'data-node-index="(\d+)"', data["tree_html"])]
        # Pre-order emission means the indices appear in ascending order, one per node.
        self.assertEqual(indices, sorted(indices))
        self.assertEqual(indices, list(range(len(indices))))
        # Every node in the markup has a truth value at every step, and vice versa.
        for values in data["steps"]:
            self.assertEqual(len(values), len(indices))

    def test_values_are_binary_and_match_node_satisfaction(self):
        result = stepper.traceSatisfactionPerStep(parse("G a"), "! a; cycle{a}", "Classic")
        data = result.getStepperViewData()

        for values in data["steps"]:
            self.assertTrue(all(v in (0, 1) for v in values))

        # 'G a' fails at state 0 (a is false there) and holds from state 1 on.
        self.assertEqual(data["steps"][0][0], 0)
        self.assertEqual(data["steps"][1][0], 1)

    def test_tree_shape_is_the_same_at_every_step(self):
        # The view only swaps classes, so a step that changed the tree's shape
        # would silently mis-colour nodes.
        result = stepper.traceSatisfactionPerStep(parse("a U (X b)"), "a; ! b; cycle{b}", "Classic")
        all_states = result.prefix_states + result.cycle_states
        shapes = {tuple(f for f, _ in state.getAllSubformulae()) for state in all_states}
        self.assertEqual(len(shapes), 1)

    def test_empty_result_gives_empty_view_data(self):
        empty = stepper.TraceSatisfactionResult([], [])
        self.assertEqual(empty.getStepperViewData(), {"tree_html": "", "steps": []})


if __name__ == "__main__":
    unittest.main()
