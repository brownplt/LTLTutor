"""Property-based tests for syntacticmutator.py -- the random syntactic mutation
used to generate answer distractors (via exercisebuilder.applyRandomMutation-
NotEquivalentTo). Previously ~16% covered.

The exercises depend on this randomness behaving well: a "mutation" that silently
returns the original formula, or that can never reach certain operators, produces
weak or duplicate distractors. These tests pin the invariants across many RNG
seeds / generated formulas.

Includes a regression test for a fixed bug where changeBinary/UnaryOperator
re-indexed the full subclass list with a candidate-list position, so they could
return the SAME operator (no mutation) and could never reach the last operator
class.

spot is mocked (sibling convention): the mutation operators are pure AST
transforms and never call spot. The one function that *would* use real semantic
equivalence, applyRandomMutationNotEquivalentTo, is exercised by patching its
equivalence check deterministically -- so this file stays fast and independent of
the SPOT kernel. (Real semantic equivalence itself is covered by
test_spotutils_realspot.py.)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

sys.modules.setdefault("spot", MagicMock())
sys.modules.setdefault("inflect", MagicMock())
sys.modules.setdefault("wordfreq", MagicMock(zipf_frequency=lambda *a, **k: 0))

import random

import ltlnode
from ltlnode import parse_ltl_string, BinaryOperatorNode, UnaryOperatorNode
import syntacticmutator as sm

try:
    from hypothesis import given, settings, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover
    HAS_HYPOTHESIS = False


def _ltl_formula_strategy():
    atoms = st.sampled_from(["a", "b", "c", "p", "q"])

    def extend(children):
        unary = st.builds(
            lambda op, f: f"({op} {f})", st.sampled_from(["G", "F", "X", "!"]), children
        )
        binary = st.builds(
            lambda op, l, r: f"({l} {op} {r})",
            st.sampled_from(["&", "|", "U", "->", "<->"]),
            children,
            children,
        )
        return unary | binary

    return st.recursive(atoms, extend, max_leaves=6)


@unittest.skipUnless(HAS_HYPOTHESIS, "hypothesis not installed")
class TestApplyRandomMutationProperties(unittest.TestCase):
    @settings(max_examples=200, deadline=None)
    @given(_ltl_formula_strategy())
    def test_never_mutates_the_original_node(self, formula):
        node = parse_ltl_string(formula)
        before = str(node)
        sm.applyRandomMutation(node)
        # applyRandomMutation deep-copies internally; the caller's node is intact.
        self.assertEqual(str(node), before)

    @settings(max_examples=200, deadline=None)
    @given(_ltl_formula_strategy())
    def test_result_is_a_valid_parseable_formula(self, formula):
        node = parse_ltl_string(formula)
        rendered = str(sm.applyRandomMutation(node))
        # A mutated formula is still syntactically valid LTL; it must round-trip.
        self.assertEqual(str(parse_ltl_string(rendered)), rendered)

    @settings(max_examples=200, deadline=None)
    @given(_ltl_formula_strategy())
    def test_mutation_never_raises(self, formula):
        node = parse_ltl_string(formula)
        try:
            sm.applyRandomMutation(node)
        except Exception as exc:  # pragma: no cover - failure path
            self.fail(f"applyRandomMutation raised {type(exc).__name__} on {formula!r}: {exc}")


class TestOperatorMutators(unittest.TestCase):
    """changeBinaryOperator / changeUnaryOperator must ALWAYS change the operator
    and must be able to reach EVERY other operator (regression for the
    off-by-position indexing bug)."""

    def test_changeBinaryOperator_always_changes_class_and_keeps_operands(self):
        node = parse_ltl_string("a & b")
        for seed in range(200):
            random.seed(seed)
            out = sm.changeBinaryOperator(node)
            self.assertIsInstance(out, BinaryOperatorNode)
            self.assertIsNot(out.__class__, node.__class__)
            self.assertEqual(str(out.left), "a")
            self.assertEqual(str(out.right), "b")

    def test_changeBinaryOperator_can_reach_every_other_operator(self):
        node = parse_ltl_string("a & b")
        expected = {c.__name__ for c in BinaryOperatorNode.__subclasses__()} - {node.__class__.__name__}
        reached = set()
        for seed in range(400):
            random.seed(seed)
            reached.add(sm.changeBinaryOperator(node).__class__.__name__)
        self.assertEqual(reached, expected)

    def test_changeUnaryOperator_always_changes_class_and_keeps_operand(self):
        node = parse_ltl_string("G a")
        for seed in range(200):
            random.seed(seed)
            out = sm.changeUnaryOperator(node)
            self.assertIsInstance(out, UnaryOperatorNode)
            self.assertIsNot(out.__class__, node.__class__)
            self.assertEqual(str(out.operand), "a")

    def test_changeUnaryOperator_can_reach_every_other_operator(self):
        node = parse_ltl_string("G a")
        expected = {c.__name__ for c in UnaryOperatorNode.__subclasses__()} - {node.__class__.__name__}
        reached = set()
        for seed in range(400):
            random.seed(seed)
            reached.add(sm.changeUnaryOperator(node).__class__.__name__)
        self.assertEqual(reached, expected)

    def test_swapOperands_swaps_left_and_right_and_keeps_class(self):
        node = parse_ltl_string("a U b")
        out = sm.swapOperands(node)
        self.assertIs(out.__class__, node.__class__)
        self.assertEqual(str(out.left), "b")
        self.assertEqual(str(out.right), "a")


class TestNotEquivalentToRetryLogic(unittest.TestCase):
    """applyRandomMutationNotEquivalentTo's retry-until-distinct logic, tested
    deterministically by controlling the equivalence oracle (no SPOT needed)."""

    def test_returns_a_mutation_when_nothing_is_equivalent(self):
        node = parse_ltl_string("a & b")
        with patch.object(sm, "isEquivalentToAny", return_value=False):
            out = sm.applyRandomMutationNotEquivalentTo(node, [node])
        self.assertIsNotNone(out)

    def test_returns_none_when_everything_is_equivalent(self):
        # If every candidate is judged equivalent, it exhausts maxAttempts and
        # gives up with None (rather than returning a bad distractor or looping).
        node = parse_ltl_string("a & b")
        with patch.object(sm, "isEquivalentToAny", return_value=True):
            out = sm.applyRandomMutationNotEquivalentTo(node, [node], maxAttempts=10)
        self.assertIsNone(out)

    def test_stops_retrying_early_once_a_distinct_mutation_is_found(self):
        # The first two candidates look equivalent, then a distinct one appears.
        # The function must stop promptly rather than burning all maxAttempts.
        node = parse_ltl_string("a & b")
        calls = {"n": 0}

        def oracle(_mutated, _targets):
            calls["n"] += 1
            return calls["n"] <= 2  # first two "equivalent", then distinct

        with patch.object(sm, "isEquivalentToAny", side_effect=oracle):
            out = sm.applyRandomMutationNotEquivalentTo(node, [node], maxAttempts=100)
        self.assertIsNotNone(out)
        self.assertLessEqual(calls["n"], 4, "did not stop early after finding a distinct mutation")


if __name__ == "__main__":
    unittest.main()
