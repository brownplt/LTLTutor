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


class TestQuestionTypeWeights(unittest.TestCase):

    def test_cold_start_is_uniform(self):
        builder = ExerciseBuilder([])
        weights = builder.calculate_question_type_weights()
        self.assertEqual(set(weights.keys()), set(ExerciseBuilder.QUESTION_TYPES))
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        for value in weights.values():
            self.assertAlmostEqual(value, 1.0 / 3, places=6)

    def test_weak_type_weighted_highest(self):
        logs = (
            make_answers(10, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(10, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL) +
            make_answers(10, correct=False, question_type=ExerciseBuilder.TRACESATYN)
        )
        builder = ExerciseBuilder(logs)
        weights = builder.calculate_question_type_weights()
        self.assertGreater(weights[ExerciseBuilder.TRACESATYN],
                           weights[ExerciseBuilder.TRACESATMC])
        self.assertGreater(weights[ExerciseBuilder.TRACESATYN],
                           weights[ExerciseBuilder.ENGLISHTOLTL])

    def test_exploration_floor_holds(self):
        """Even a type the student always gets right keeps at least the floor."""
        logs = (
            make_answers(50, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(50, correct=False, question_type=ExerciseBuilder.TRACESATYN) +
            make_answers(50, correct=False, question_type=ExerciseBuilder.ENGLISHTOLTL)
        )
        builder = ExerciseBuilder(logs)
        weights = builder.calculate_question_type_weights()
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=6)
        for qtype, value in weights.items():
            self.assertGreaterEqual(value, ExerciseBuilder.QUESTION_TYPE_FLOOR - 1e-9,
                                    f"{qtype} fell below the exploration floor: {value}")

    def test_unknown_question_types_ignored(self):
        logs = make_answers(10, correct=False, question_type="not-a-real-type")
        builder = ExerciseBuilder(logs)
        weights = builder.calculate_question_type_weights()
        for value in weights.values():
            self.assertAlmostEqual(value, 1.0 / 3, places=6)

    def test_choose_question_kind_returns_valid_type(self):
        builder = ExerciseBuilder([])
        for _ in range(20):
            self.assertIn(builder.choose_question_kind(), ExerciseBuilder.QUESTION_TYPES)

    def test_choose_question_kind_biased_toward_weak_type(self):
        """With a heavily skewed history, the weak type should dominate draws."""
        logs = (
            make_answers(30, correct=True, question_type=ExerciseBuilder.TRACESATMC) +
            make_answers(30, correct=True, question_type=ExerciseBuilder.ENGLISHTOLTL) +
            make_answers(30, correct=False, question_type=ExerciseBuilder.TRACESATYN)
        )
        builder = ExerciseBuilder(logs)
        draws = [builder.choose_question_kind() for _ in range(500)]
        yn_share = draws.count(ExerciseBuilder.TRACESATYN) / len(draws)
        self.assertGreater(yn_share, 0.4)


if __name__ == '__main__':
    unittest.main()
