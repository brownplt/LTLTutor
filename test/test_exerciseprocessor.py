"""Tests for exerciseprocessor.py -- exercise loading, randomization, and
trace-to-render-data conversion.

Focus areas (complementing the existing test_trace_canonicalization.py and
test_formula_literals.py, which already cover canonicalizeSpotTrace /
getFormulaLiterals):

  * randomize_questions -- the option/question shuffling that runs on EVERY
    exercise load. A bug here (dropping an option, losing the correct answer,
    duplicating a question) would silently corrupt what students see, so the
    invariants are checked across many RNG seeds.
  * removeORs / choosePathFromWord -- resolve OR branches in a trace/formula by
    random choice; must always leave a valid, OR-free result.
  * change_traces_to_render_data -- attaches SVG render data to trace questions.

These functions are pure Python; spot is mocked (as in sibling tests) purely so
the transitive `import spot` succeeds.
"""

import copy
import json
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

sys.modules.setdefault("spot", MagicMock())
sys.modules.setdefault("inflect", MagicMock())
sys.modules.setdefault("wordfreq", MagicMock(zipf_frequency=lambda *a, **k: 0))

import random

import exerciseprocessor as ep
import ltlnode


def _option(text, correct=False, misconceptions=None):
    return {"option": text, "isCorrect": correct, "misconceptions": misconceptions or []}


def _sample_questions():
    return [
        {
            "question": "The engine is eventually on.",
            "type": "englishtoltl",
            "options": [
                _option("F e", correct=True),
                _option("G e"),
                _option("e U f"),
                _option("X e"),
            ],
        },
        {
            "question": "The light stays on forever.",
            "type": "englishtoltl",
            "options": [
                _option("G l", correct=True),
                _option("F l"),
                _option("l"),
            ],
        },
    ]


def _option_multiset(question):
    return sorted(json.dumps(o, sort_keys=True) for o in question["options"])


def _has_or_node(node):
    if isinstance(node, ltlnode.OrNode):
        return True
    if isinstance(node, ltlnode.UnaryOperatorNode):
        return _has_or_node(node.operand)
    if isinstance(node, ltlnode.BinaryOperatorNode):
        return _has_or_node(node.left) or _has_or_node(node.right)
    return False


class TestRandomizeQuestions(unittest.TestCase):
    """randomize_questions runs on every exercise load; it must be a pure
    permutation -- never drop, duplicate, or corrupt questions or options."""

    def test_preserves_questions_and_options_across_seeds(self):
        original = _sample_questions()
        original_questions = sorted(q["question"] for q in original)
        original_option_sets = {q["question"]: _option_multiset(q) for q in original}

        for seed in range(50):
            random.seed(seed)
            data = copy.deepcopy(original)
            result = ep.randomize_questions(data)

            # Same number of questions, same set of question prompts.
            self.assertEqual(len(result), len(original))
            self.assertEqual(sorted(q["question"] for q in result), original_questions)

            # Each question keeps EXACTLY its original option multiset (a
            # permutation): nothing added, dropped, duplicated, or edited.
            for q in result:
                self.assertEqual(
                    _option_multiset(q),
                    original_option_sets[q["question"]],
                    f"options corrupted for {q['question']!r} at seed {seed}",
                )

    def test_preserves_single_correct_option(self):
        for seed in range(50):
            random.seed(seed)
            data = copy.deepcopy(_sample_questions())
            result = ep.randomize_questions(data)
            for q in result:
                correct = [o for o in q["options"] if o["isCorrect"]]
                self.assertEqual(len(correct), 1, f"correct-option count wrong at seed {seed}")

    def test_actually_reorders_for_some_seed(self):
        # Sanity: the function is capable of producing a non-identity order,
        # otherwise the "randomization" would be a silent no-op.
        original = _sample_questions()
        saw_reorder = False
        for seed in range(50):
            random.seed(seed)
            data = copy.deepcopy(original)
            result = ep.randomize_questions(data)
            orders = [[o["option"] for o in q["options"]] for q in result]
            original_orders = [[o["option"] for o in q["options"]] for q in original]
            if orders != original_orders or [q["question"] for q in result] != [
                q["question"] for q in original
            ]:
                saw_reorder = True
                break
        self.assertTrue(saw_reorder, "randomize_questions never changed any order in 50 seeds")


class TestRemoveORs(unittest.TestCase):
    def test_choose_path_picks_one_disjunct(self):
        seen = set()
        for seed in range(30):
            random.seed(seed)
            seen.add(ep.choosePathFromWord("a | b"))
        # Only the two disjuncts are ever produced, and both are reachable.
        self.assertEqual(seen, {"a", "b"})

    def test_no_or_remains_in_result(self):
        formulas = ["a | b", "G(a | b) & (c | d)", "F(a | b | c)", "(a | b) U c"]
        for formula in formulas:
            for seed in range(20):
                random.seed(seed)
                result = ep.choosePathFromWord(formula)
                node = ltlnode.parse_ltl_string(result)
                self.assertFalse(
                    _has_or_node(node),
                    f"OR survived in {result!r} (from {formula!r}, seed {seed})",
                )

    def test_or_free_formula_is_preserved(self):
        for formula in ["G a", "a U b", "X (a & b)", "F a"]:
            random.seed(0)
            result = ep.choosePathFromWord(formula)
            # Same AST (string round-trips through the parser identically).
            self.assertEqual(
                str(ltlnode.parse_ltl_string(result)),
                str(ltlnode.parse_ltl_string(formula)),
            )


class TestChangeTracesToRenderData(unittest.TestCase):
    def test_mc_options_get_render_data_without_parens(self):
        data = [
            {
                "type": "tracesatisfaction_mc",
                "question": "G a",
                "options": [
                    _option("a; cycle{a}", correct=True),
                    _option("(a); cycle{(a & b)}"),
                ],
            }
        ]
        random.seed(0)
        result = ep.change_traces_to_render_data(copy.deepcopy(data), literals=["a", "b"])
        for option in result[0]["options"]:
            self.assertIn("prefix", option["trace_data"])
            self.assertIn("cycle", option["trace_data"])
            self.assertNotIn("(", option["option"])
            self.assertNotIn(")", option["option"])

    def test_yn_trace_gets_render_data_without_parens(self):
        data = [
            {
                "type": "tracesatisfaction_yn",
                "question": "G a",
                "trace": "(a); cycle{a}",
                "answer": True,
            }
        ]
        random.seed(0)
        result = ep.change_traces_to_render_data(copy.deepcopy(data), literals=["a"])
        q = result[0]
        self.assertIn("prefix", q["trace_data"])
        self.assertIn("cycle", q["trace_data"])
        self.assertNotIn("(", q["trace"])

    def test_englishtoltl_questions_are_left_untouched(self):
        data = [{"type": "englishtoltl", "question": "F a", "options": [_option("F a", True)]}]
        result = ep.change_traces_to_render_data(copy.deepcopy(data), literals=["a"])
        self.assertNotIn("trace_data", result[0])
        self.assertEqual(result[0]["options"][0]["option"], "F a")


class TestNodeReprRoundTrip(unittest.TestCase):
    def test_spot_trace_to_node_reprs_structure(self):
        nr = ep.spotTraceToNodeReprs("a; cycle{b}")
        self.assertEqual([str(s) for s in nr["prefix_states"]], ["a"])
        # spotTraceToNodeReprs appends the first cycle state again to close the loop.
        self.assertEqual([str(s) for s in nr["cycle_states"]], ["b", "b"])

    def test_empty_trace_yields_empty_list(self):
        self.assertEqual(ep.spotTraceToNodeReprs("   "), [])

    def test_round_trip_rebuilds_trace(self):
        nr = ep.spotTraceToNodeReprs("a; cycle{b}")
        rebuilt = ep.nodeReprListsToSpotTrace(nr["prefix_states"], nr["cycle_states"])
        self.assertEqual(rebuilt, "a;cycle{b;b}")


if __name__ == "__main__":
    unittest.main()
