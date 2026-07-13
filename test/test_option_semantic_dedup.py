"""Distractor options must be pairwise semantically distinct.

Misconception mutations are filtered against the *answer* (codebook drops
mutations equivalent to the original), but two different misconceptions can
produce formulas equivalent to each other — e.g. mutating G(F d) gives both
"G d" (dropped F) and "G (G d)" (F->G swap), and G is idempotent. Showing
both wastes a distractor slot and makes misconception attribution arbitrary,
so the option builder must merge them.

The equivalence oracle (LTLNode.equiv -> SPOT) is patched deterministically,
following test_syntacticmutator_pbt.py.

Run with:
    python -m pytest test/test_option_semantic_dedup.py -v
"""

import unittest
import sys
import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.modules['spot'] = MagicMock()

import exercisebuilder as eb
import ltlnode
from ltlnode import parse_ltl_string, LTLNode


def _fake_misconceptions(*pairs):
    """Build getAllApplicableMisconceptions-shaped results from
    (formula_string, code) pairs."""
    return [SimpleNamespace(node=parse_ltl_string(f), misconception=code)
            for f, code in pairs]


# G is idempotent: "G d" and "G (G d)" denote the same property. Everything
# else is equivalent only to itself.
_EQUIV_CLASS = {"(G d)", "(G (G d))"}


def _fake_equiv(f1, f2):
    a, b = str(f1), str(f2)
    if a == b:
        return True
    return a in _EQUIV_CLASS and b in _EQUIV_CLASS


class TestSemanticOptionDedup(unittest.TestCase):

    def _options(self, misconceptions):
        builder = eb.ExerciseBuilder([])
        with patch.object(eb.codebook, "getAllApplicableMisconceptions",
                          return_value=misconceptions), \
             patch.object(LTLNode, "equiv", _fake_equiv), \
             patch.object(eb, "applyRandomMutationNotEquivalentTo",
                          return_value=None):
            return builder.get_options_with_misconceptions_as_formula("G(F d)")

    def test_equivalent_distractors_are_merged(self):
        options = self._options(_fake_misconceptions(
            ("G d", "MissingFinally"),
            ("G(G d)", "SwappedFinallyForGlobally"),
            ("F d", "MissingGlobally"),
        ))
        texts = [o["option"] for o in options if not o["isCorrect"]]
        in_class = [t for t in texts if t in _EQUIV_CLASS]
        self.assertEqual(len(in_class), 1,
                         f"expected one representative of {_EQUIV_CLASS}, got {texts}")

    def test_merged_option_keeps_both_misconception_codes(self):
        options = self._options(_fake_misconceptions(
            ("G d", "MissingFinally"),
            ("G(G d)", "SwappedFinallyForGlobally"),
        ))
        merged = next(o for o in options if o["option"] in _EQUIV_CLASS)
        self.assertCountEqual(
            merged["misconceptions"],
            ["MissingFinally", "SwappedFinallyForGlobally"])

    def test_distinct_distractors_survive(self):
        options = self._options(_fake_misconceptions(
            ("G d", "MissingFinally"),
            ("F d", "MissingGlobally"),
        ))
        texts = sorted(o["option"] for o in options if not o["isCorrect"])
        self.assertEqual(texts, ["(F d)", "(G d)"])

    def test_correct_option_still_present(self):
        options = self._options(_fake_misconceptions(
            ("G d", "MissingFinally"),
            ("G(G d)", "SwappedFinallyForGlobally"),
        ))
        correct = [o for o in options if o["isCorrect"]]
        self.assertEqual(len(correct), 1)
        self.assertEqual(correct[0]["option"], "(G (F d))")


if __name__ == "__main__":
    unittest.main()
