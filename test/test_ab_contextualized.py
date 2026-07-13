"""Tests for the abstract-vs-contextualized A/B question building.

The contextualized arm must pose the SAME formula (modulo literal renaming)
as the abstract arm would, and every english-to-ltl question must carry a
translation_mode so student responses can be analyzed per condition.

Run with:
    python -m pytest test/test_ab_contextualized.py -v
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from exercisebuilder import ExerciseBuilder
import ltltoeng_contextualized as ctx
from ltlnode import parse_ltl_string


class StubBuilder(ExerciseBuilder):
    """ExerciseBuilder whose option generation is stubbed out, so question
    building can be tested without SPOT or a database."""

    def __init__(self):
        super().__init__([])

    def get_options_with_misconceptions_as_formula(self, answer):
        return [{"option": answer, "isCorrect": True, "misconceptions": []}]


class TestGenContextualizedAnswer(unittest.TestCase):

    def setUp(self):
        self.builder = StubBuilder()

    def test_remaps_onto_theme_literals(self):
        result = self.builder.gen_contextualized_answer("G(z -> F k)")
        self.assertIsNotNone(result)
        lits = ctx.collect_literals(parse_ltl_string(result))
        self.assertTrue(lits.issubset(set(ctx.THEMES["lights"].literals)))

    def test_returns_none_for_unparseable(self):
        self.assertIsNone(self.builder.gen_contextualized_answer("G(z -> "))

    def test_returns_none_for_too_many_literals(self):
        self.assertIsNone(
            self.builder.gen_contextualized_answer("(d & e) | (h & i) | j"))


class TestTranslationModeLogging(unittest.TestCase):

    def setUp(self):
        self.builder = StubBuilder()

    def test_abstract_question_marks_mode(self):
        q = self.builder.build_english_to_ltl_question("G(z -> F k)")
        self.assertIsNotNone(q)
        self.assertEqual(q["translation_mode"], "abstract")

    def test_contextualized_question_marks_mode(self):
        themed = self.builder.gen_contextualized_answer("G(z -> F k)")
        q = self.builder.build_english_to_ltl_question(themed, contextualized=True)
        self.assertIsNotNone(q)
        self.assertEqual(q["translation_mode"], "contextualized")
        self.assertIn("light", q["question"].lower())

    def test_contextualized_question_has_no_quoted_literals(self):
        """The contextualized sentence must not leak abstract 'x' phrasing."""
        themed = self.builder.gen_contextualized_answer("G(z -> (k U j))")
        q = self.builder.build_english_to_ltl_question(themed, contextualized=True)
        for lit in ctx.THEMES["lights"].literals:
            self.assertNotIn(f"'{lit}'", q["question"])


if __name__ == "__main__":
    unittest.main()
