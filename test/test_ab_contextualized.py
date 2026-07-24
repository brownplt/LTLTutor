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


class TestDeonticArm(unittest.TestCase):
    """The abac (deontic audit) arm: same formula, policy framing, own mode."""

    def setUp(self):
        self.builder = StubBuilder()

    def test_remaps_onto_abac_literals(self):
        result = self.builder.gen_contextualized_answer(
            "G(z -> F k)", theme_name="abac")
        self.assertIsNotNone(result)
        lits = ctx.collect_literals(parse_ltl_string(result))
        self.assertTrue(lits.issubset(set(ctx.THEMES["abac"].literals)))

    def test_deontic_question_marks_mode(self):
        themed = self.builder.gen_contextualized_answer(
            "G(z -> F k)", theme_name="abac")
        q = self.builder.build_english_to_ltl_question(themed, theme_name="abac")
        self.assertIsNotNone(q)
        self.assertEqual(q["translation_mode"], "contextualizeddeontic")

    def test_deontic_question_has_preamble_and_obligation(self):
        themed = self.builder.gen_contextualized_answer(
            "G(z -> F k)", theme_name="abac")
        q = self.builder.build_english_to_ltl_question(themed, theme_name="abac")
        ## The stance and the "company policy" noun travel beside the sentence
        ## rather than inside it: they belong to the question being asked, so
        ## the UI folds them into the prompt and leaves the sentence alone as
        ## the one thing to formalize.
        self.assertEqual(q["preamble"], ctx.THEMES["abac"].preamble)
        self.assertEqual(q["rule_noun"], ctx.THEMES["abac"].rule_noun)
        self.assertNotIn(ctx.THEMES["abac"].preamble, q["question"])
        self.assertIn("must", q["question"])

    def test_themed_question_carries_a_key_for_its_letters(self):
        """A themed sentence is in words while its options are in letters, so
        the question must state the correspondence: otherwise it also tests
        whether the student can guess that 'd' means the document is *open*."""
        for theme_name in ("abac", "lights"):
            with self.subTest(theme=theme_name):
                themed = self.builder.gen_contextualized_answer(
                    "G(z -> F k)", theme_name=theme_name)
                q = self.builder.build_english_to_ltl_question(
                    themed, theme_name=theme_name)
                used = ctx.collect_literals(parse_ltl_string(themed))
                self.assertEqual({e["literal"] for e in q["legend"]}, used)
                theme = ctx.THEMES[theme_name]
                for entry in q["legend"]:
                    self.assertEqual(entry["meaning"],
                                     theme.literals[entry["literal"]][0])

    def test_key_omits_letters_the_formula_never_uses(self):
        """Listing unused attributes would hint at states the question does
        not involve."""
        themed = self.builder.gen_contextualized_answer("G(z -> F k)", theme_name="abac")
        q = self.builder.build_english_to_ltl_question(themed, theme_name="abac")
        self.assertEqual(len(q["legend"]), 2)

    def test_abstract_arm_has_no_key(self):
        """Abstract prose already quotes its literals, so there is nothing to
        look up, and adding a key there would change the control arm."""
        q = self.builder.build_english_to_ltl_question("G(z -> F k)")
        self.assertEqual(q["legend"], [])
        self.assertEqual(q["preamble"], "")

    def test_deontic_question_has_no_quoted_literals(self):
        themed = self.builder.gen_contextualized_answer(
            "G(z -> (k U j))", theme_name="abac")
        q = self.builder.build_english_to_ltl_question(themed, theme_name="abac")
        for lit in ctx.THEMES["abac"].literals:
            self.assertNotIn(f"'{lit}'", q["question"])

    def test_lights_arm_has_no_preamble(self):
        """Only the deontic arm carries a stance-setting preamble; the lights
        arm must keep producing exactly what it produced before the third arm
        existed, so historical responses stay comparable."""
        themed = self.builder.gen_contextualized_answer("G(z -> F k)")
        q = self.builder.build_english_to_ltl_question(themed, contextualized=True)
        self.assertNotIn("\n", q["question"])
        self.assertEqual(q["translation_mode"], "contextualized")


if __name__ == "__main__":
    unittest.main()
