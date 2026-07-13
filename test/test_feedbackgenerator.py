"""Tests for feedbackgenerator.FeedbackGenerator (real SPOT).

FeedbackGenerator produces the semantic feedback shown to a student after an
English-to-LTL answer: it decides how the student's chosen formula relates to
the correct one (equivalent / one implies the other / disjoint / overlapping)
and generates counterexample traces that distinguish them. It was previously at
0% coverage despite being on the answer-feedback path.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import realspot

_loaded = realspot.load_real("spotutils", "feedbackgenerator")
SPOT_AVAILABLE = _loaded is not None
if SPOT_AVAILABLE:
    spotutils, feedbackgenerator = _loaded
    FeedbackGenerator = feedbackgenerator.FeedbackGenerator


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestRelationPredicates(unittest.TestCase):
    def test_equivalent_formulas(self):
        fg = FeedbackGenerator(correct="G a", student="G G a")
        self.assertTrue(fg.equivalent())
        # Equivalence means mutual implication in both directions.
        self.assertTrue(fg.correctAnswerContained())
        self.assertTrue(fg.correctAnswerSubsumes())
        self.assertFalse(fg.disjoint())

    def test_disjoint_formulas(self):
        # G a and G !a share no satisfying trace.
        fg = FeedbackGenerator(correct="G a", student="G ! a")
        self.assertTrue(fg.disjoint())
        self.assertFalse(fg.equivalent())
        self.assertFalse(fg.correctAnswerContained())
        self.assertFalse(fg.correctAnswerSubsumes())

    def test_student_answer_is_strictly_stronger(self):
        # student 'a' implies correct 'F a', but not vice versa.
        fg = FeedbackGenerator(correct="F a", student="a")
        self.assertTrue(fg.correctAnswerSubsumes())   # student => correct
        self.assertFalse(fg.correctAnswerContained())  # correct =/=> student
        self.assertFalse(fg.equivalent())
        self.assertFalse(fg.disjoint())

    def test_student_answer_is_strictly_weaker(self):
        # correct 'a' implies student 'F a', but not vice versa.
        fg = FeedbackGenerator(correct="a", student="F a")
        self.assertTrue(fg.correctAnswerContained())   # correct => student
        self.assertFalse(fg.correctAnswerSubsumes())    # student =/=> correct
        self.assertFalse(fg.equivalent())
        self.assertFalse(fg.disjoint())

    def test_overlapping_but_independent(self):
        # 'a' and 'b': neither implies the other, but a & b is satisfiable.
        fg = FeedbackGenerator(correct="a", student="b")
        self.assertFalse(fg.equivalent())
        self.assertFalse(fg.disjoint())
        self.assertFalse(fg.correctAnswerContained())
        self.assertFalse(fg.correctAnswerSubsumes())


@unittest.skipUnless(SPOT_AVAILABLE, "real SPOT library not available")
class TestCounterexampleWords(unittest.TestCase):
    def test_equivalent_formulas_have_no_counterexamples(self):
        fg = FeedbackGenerator(correct="G a", student="G G a")
        self.assertEqual(fg.getCEWords(), [])

    def test_every_counterexample_distinguishes_the_two_formulas(self):
        # The defining property of a counterexample word: it must be satisfied
        # by exactly one of {correct, student}. If a "counterexample" satisfied
        # both or neither, it would not demonstrate any difference to a student.
        pairs = [
            ("G a", "G ! a"),   # disjoint
            ("F a", "a"),        # student stronger
            ("a", "F a"),        # student weaker
            ("a", "b"),          # overlapping/independent
            ("a & b", "a"),      # correct stronger
        ]
        for correct, student in pairs:
            fg = FeedbackGenerator(correct=correct, student=student)
            words = fg.getCEWords()
            self.assertGreater(
                len(words), 0, f"expected counterexamples for {correct} vs {student}"
            )
            for word in words:
                sat_correct = spotutils.is_trace_satisfied(trace=word, formula=correct)
                sat_student = spotutils.is_trace_satisfied(trace=word, formula=student)
                self.assertNotEqual(
                    sat_correct,
                    sat_student,
                    f"counterexample {word!r} fails to distinguish "
                    f"{correct!r} (sat={sat_correct}) from {student!r} (sat={sat_student})",
                )

    def test_disjoint_counterexamples_satisfy_student_not_correct(self):
        # For disjoint answers the generated words are accepted by the student's
        # (wrong) formula, illustrating traces the student wrongly admits.
        fg = FeedbackGenerator(correct="G a", student="G ! a")
        for word in fg.getCEWords():
            self.assertTrue(spotutils.is_trace_satisfied(trace=word, formula="G ! a"))
            self.assertFalse(spotutils.is_trace_satisfied(trace=word, formula="G a"))


if __name__ == "__main__":
    unittest.main()
