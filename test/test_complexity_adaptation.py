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
    """Mock of a student_responses row, one per (question, misconception)."""

    def __init__(self, timestamp, question_text="q", correct_answer=False,
                 misconception=""):
        self.timestamp = timestamp
        self.question_text = question_text
        self.correct_answer = correct_answer
        self.misconception = misconception


def make_answers(n, correct, start=None, minutes_apart=10):
    """Build n distinct answers (distinct question_text and timestamps)."""
    if start is None:
        start = datetime.datetime.now() - datetime.timedelta(hours=5)
    return [
        MockAnswerLog(
            timestamp=start + datetime.timedelta(minutes=i * minutes_apart),
            question_text=f"q-{correct}-{i}",
            correct_answer=correct
        )
        for i in range(n)
    ]


class TestDistinctAnswers(unittest.TestCase):

    def test_misconception_rows_collapse_to_one_answer(self):
        """A wrong answer logged as 3 misconception rows (with near-identical
        timestamps from separate now() calls) must count as a single answer."""
        now = datetime.datetime.now()
        logs = [
            MockAnswerLog(now + datetime.timedelta(milliseconds=5 * i),
                          question_text="same-question",
                          correct_answer=False, misconception=f"M{i}")
            for i in range(3)
        ]
        builder = ExerciseBuilder(logs)
        self.assertEqual(len(builder._distinct_answers()), 1)

    def test_same_question_after_window_counts_again(self):
        now = datetime.datetime.now()
        logs = [
            MockAnswerLog(now, question_text="same-question"),
            MockAnswerLog(now + datetime.timedelta(minutes=10), question_text="same-question"),
        ]
        builder = ExerciseBuilder(logs)
        self.assertEqual(len(builder._distinct_answers()), 2)


class TestCorrectAnswerCoercion(unittest.TestCase):

    def test_bool_and_string_representations(self):
        builder = ExerciseBuilder([])
        self.assertTrue(builder._log_is_correct(MockAnswerLog(None, correct_answer=True)))
        self.assertTrue(builder._log_is_correct(MockAnswerLog(None, correct_answer='True')))
        self.assertTrue(builder._log_is_correct(MockAnswerLog(None, correct_answer='true')))
        self.assertFalse(builder._log_is_correct(MockAnswerLog(None, correct_answer=False)))
        self.assertFalse(builder._log_is_correct(MockAnswerLog(None, correct_answer='False')))
        self.assertFalse(builder._log_is_correct(MockAnswerLog(None, correct_answer=None)))


class TestComplexityUpdate(unittest.TestCase):

    def test_steps_up_on_high_accuracy(self):
        builder = ExerciseBuilder(make_answers(10, correct=True), complexity=5)
        self.assertEqual(builder.update_complexity(), 6)

    def test_steps_down_on_low_accuracy(self):
        builder = ExerciseBuilder(make_answers(10, correct=False), complexity=5)
        self.assertEqual(builder.update_complexity(), 4)

    def test_no_step_on_middling_accuracy(self):
        logs = make_answers(6, correct=True) + make_answers(4, correct=False)
        builder = ExerciseBuilder(logs, complexity=5)
        self.assertEqual(builder.update_complexity(), 5)

    def test_needs_minimum_answers_to_move(self):
        builder = ExerciseBuilder(make_answers(3, correct=True), complexity=5)
        self.assertEqual(builder.update_complexity(), 5)

    def test_clamped_to_bounds(self):
        up = ExerciseBuilder(make_answers(10, correct=True),
                             complexity=ExerciseBuilder.COMPLEXITY_MAX)
        self.assertEqual(up.update_complexity(), ExerciseBuilder.COMPLEXITY_MAX)

        down = ExerciseBuilder(make_answers(10, correct=False),
                               complexity=ExerciseBuilder.COMPLEXITY_MIN)
        self.assertEqual(down.update_complexity(), ExerciseBuilder.COMPLEXITY_MIN)

    def test_out_of_range_persisted_value_is_clamped(self):
        builder = ExerciseBuilder([], complexity=99)
        self.assertLessEqual(builder.complexity, ExerciseBuilder.COMPLEXITY_MAX)
        builder = ExerciseBuilder([], complexity=-4)
        self.assertGreaterEqual(builder.complexity, ExerciseBuilder.COMPLEXITY_MIN)

    def test_only_recent_window_counts(self):
        """Old failures outside the 10-answer window must not drag complexity down."""
        old_failures = make_answers(10, correct=False,
                                    start=datetime.datetime.now() - datetime.timedelta(days=10))
        recent_successes = make_answers(10, correct=True)
        builder = ExerciseBuilder(old_failures + recent_successes, complexity=5)
        self.assertEqual(builder.update_complexity(), 6)


if __name__ == '__main__':
    unittest.main()
