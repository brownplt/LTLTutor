import unittest
import sys
import os
import datetime

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from exercisebuilder import ExerciseBuilder


class MockAnswerLog:
    """Mock of a student_responses row."""

    def __init__(self, timestamp, question_text="q", question_type=None,
                 correct_answer=False, misconception=""):
        self.timestamp = timestamp
        self.question_text = question_text
        self.question_type = question_type
        self.correct_answer = correct_answer
        self.misconception = misconception


def make_answers(n, correct, question_type):
    """Build n distinct answers of one question type."""
    start = datetime.datetime.now() - datetime.timedelta(hours=5)
    return [
        MockAnswerLog(
            timestamp=start + datetime.timedelta(minutes=i * 10),
            question_text=f"q-{question_type}-{correct}-{i}",
            question_type=question_type,
            correct_answer=correct
        )
        for i in range(n)
    ]


TRACE_FAMILY = ExerciseBuilder.TRACESAT_FAMILY
ENG_FAMILY = ExerciseBuilder.ENGLISHTOLTL_FAMILY


class TestQuestionFamilyWeights(unittest.TestCase):
    """Selection adapts between the two skills, not between presentation
    variants of one of them."""

    def test_family_of_covers_every_question_type(self):
        for qtype in ExerciseBuilder.QUESTION_TYPES:
            self.assertIn(ExerciseBuilder.family_of(qtype),
                          ExerciseBuilder.QUESTION_FAMILIES)
        self.assertIsNone(ExerciseBuilder.family_of("not-a-real-type"))

    def test_cold_start_is_an_even_family_split(self):
        weights = ExerciseBuilder([]).calculate_question_family_weights()
        self.assertEqual(set(weights.keys()), set(ExerciseBuilder.QUESTION_FAMILIES))
        for value in weights.values():
            self.assertAlmostEqual(value, 0.5, places=6)

    def test_trace_subtypes_do_not_outvote_english_to_ltl(self):
        """The trace family gets one share of the mass, not one per subtype.
        Equally wrong on all three types used to mean 2/3 trace, 1/3
        english-to-LTL. (Not exactly 0.5 apiece: the trace family has twice
        the attempts here, so Laplace smoothing pulls its rate less far
        toward 0.5 than the single english-to-LTL type's.)"""
        logs = (
            make_answers(20, correct=False, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(20, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(20, correct=False, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        weights = ExerciseBuilder(logs).calculate_question_family_weights()
        self.assertAlmostEqual(weights[TRACE_FAMILY], 0.5, delta=0.02)
        self.assertAlmostEqual(weights[ENG_FAMILY], 0.5, delta=0.02)

    def test_weak_family_weighted_highest(self):
        logs = (
            make_answers(10, correct=False, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(10, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(10, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        weights = ExerciseBuilder(logs).calculate_question_family_weights()
        self.assertGreater(weights[TRACE_FAMILY], weights[ENG_FAMILY])

    def test_attempts_are_pooled_across_a_family(self):
        """A family's score comes from its combined record, so a subtype the
        student aces cannot be offset by hammering the other one."""
        mixed = ExerciseBuilder(
            make_answers(10, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(10, correct=False, question_type=ExerciseBuilder.TRACESATYN)
        ).calculate_question_family_weights()
        pooled = ExerciseBuilder(
            make_answers(10, correct=True, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(10, correct=False, question_type=ExerciseBuilder.TRACESATMC)
        ).calculate_question_family_weights()
        self.assertAlmostEqual(mixed[TRACE_FAMILY], pooled[TRACE_FAMILY], places=6)

    def test_exploration_floor_holds(self):
        """Even a family the student always gets right keeps at least the floor."""
        logs = (
            make_answers(50, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(50, correct=True, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(50, correct=False, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        weights = ExerciseBuilder(logs).calculate_question_family_weights()
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        for family, value in weights.items():
            self.assertGreaterEqual(value, ExerciseBuilder.QUESTION_FAMILY_FLOOR - 1e-9,
                                    f"{family} fell below the exploration floor: {value}")

    def test_unknown_question_types_ignored(self):
        logs = make_answers(10, correct=False, question_type="not-a-real-type")
        weights = ExerciseBuilder(logs).calculate_question_family_weights()
        for value in weights.values():
            self.assertAlmostEqual(value, 0.5, places=6)


class TestQuestionTypeWeights(unittest.TestCase):

    def test_cold_start_splits_the_family_mass_evenly(self):
        weights = ExerciseBuilder([]).calculate_question_type_weights()
        self.assertEqual(set(weights.keys()), set(ExerciseBuilder.QUESTION_TYPES))
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        self.assertAlmostEqual(weights[ExerciseBuilder.ENGLISHTOLTL], 0.5, places=6)
        self.assertAlmostEqual(weights[ExerciseBuilder.TRACESATMC], 0.25, places=6)
        self.assertAlmostEqual(weights[ExerciseBuilder.TRACESATYN], 0.25, places=6)

    def test_trace_subtypes_stay_even_however_they_are_answered(self):
        """mc and yn are presentation variants, so nothing drills one over the
        other: their error rates aren't comparable (yn is a coin flip)."""
        logs = (
            make_answers(30, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(30, correct=False, question_type=ExerciseBuilder.TRACESATYN)
        )
        weights = ExerciseBuilder(logs).calculate_question_type_weights()
        self.assertAlmostEqual(weights[ExerciseBuilder.TRACESATMC],
                               weights[ExerciseBuilder.TRACESATYN], places=6)

    def test_type_weights_agree_with_family_weights(self):
        logs = (
            make_answers(15, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(15, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        builder = ExerciseBuilder(logs)
        families = builder.calculate_question_family_weights()
        types = builder.calculate_question_type_weights()
        for family, subtypes in ExerciseBuilder.QUESTION_FAMILIES.items():
            self.assertAlmostEqual(sum(types[t] for t in subtypes),
                                   families[family], places=6)

    def test_english_to_ltl_never_starved(self):
        """The complaint that motivated the family split: a student who is good
        at english-to-LTL still sees it often enough for all three framing arms
        to appear (each arm is a third of this share)."""
        logs = (
            make_answers(50, correct=False, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(50, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(50, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        weights = ExerciseBuilder(logs).calculate_question_type_weights()
        self.assertGreaterEqual(weights[ExerciseBuilder.ENGLISHTOLTL],
                                ExerciseBuilder.QUESTION_FAMILY_FLOOR - 1e-9)

    def test_choose_question_kind_returns_valid_type(self):
        builder = ExerciseBuilder([])
        for _ in range(20):
            self.assertIn(builder.choose_question_kind(), ExerciseBuilder.QUESTION_TYPES)

    def test_choose_question_kind_biased_toward_weak_family(self):
        """With a heavily skewed history, the weak family should dominate draws."""
        logs = (
            make_answers(30, correct=False, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(30, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(30, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        builder = ExerciseBuilder(logs)
        draws = [builder.choose_question_kind() for _ in range(500)]
        trace_share = sum(
            1 for d in draws if ExerciseBuilder.family_of(d) == TRACE_FAMILY
        ) / len(draws)
        self.assertGreater(trace_share, 0.6)

    def test_choose_question_kind_draws_both_families_at_cold_start(self):
        builder = ExerciseBuilder([])
        draws = [builder.choose_question_kind() for _ in range(500)]
        eng_share = draws.count(ExerciseBuilder.ENGLISHTOLTL) / len(draws)
        self.assertGreater(eng_share, 0.4)
        self.assertLess(eng_share, 0.6)


if __name__ == '__main__':
    unittest.main()
