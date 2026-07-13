import unittest
import sys
import os
import datetime

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot the same way the rest of the suite does, so ExerciseBuilder can be
# constructed without SPOT or a database.
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from exercisebuilder import ExerciseBuilder


class FakeLog:
    def __init__(self, timestamp, question_type, correct_answer, misconception=''):
        self.timestamp = timestamp
        self.question_type = question_type
        self.correct_answer = correct_answer
        self.misconception = misconception
        self.question_text = 'G(a)'


class TestComplexityBand(unittest.TestCase):

    def _band(self, complexity):
        b = ExerciseBuilder([])
        b.complexity = complexity
        return b._complexity_band()

    def test_bands_across_range(self):
        # Default bounds are [3, 12]: lowest third Beginner, middle Intermediate,
        # top third Advanced.
        self.assertEqual(self._band(3), "Beginner")
        self.assertEqual(self._band(5), "Beginner")
        self.assertEqual(self._band(6), "Intermediate")
        self.assertEqual(self._band(8), "Intermediate")
        self.assertEqual(self._band(9), "Advanced")
        self.assertEqual(self._band(12), "Advanced")


class TestProfileSnapshot(unittest.TestCase):

    def test_empty_history_defaults(self):
        snap = ExerciseBuilder([]).get_profile_snapshot()
        self.assertEqual(snap['complexity_min'], ExerciseBuilder.COMPLEXITY_MIN)
        self.assertEqual(snap['complexity_max'], ExerciseBuilder.COMPLEXITY_MAX)
        # Three question types, uniform selection weight, summing to 1.
        weights = snap['question_type_weights']
        self.assertEqual(len(weights), 3)
        self.assertAlmostEqual(sum(weights.values()), 1.0, places=5)

    def test_misconception_snapshot_sorted_desc_and_prefix_stripped(self):
        snap = ExerciseBuilder([]).get_profile_snapshot()
        names = [m['name'] for m in snap['misconception_snapshot']]
        vals = [m['weight'] for m in snap['misconception_snapshot']]
        # No raw enum prefixes leak into the view model.
        self.assertFalse(any('MisconceptionCode.' in n for n in names))
        # Descending by weight.
        self.assertEqual(vals, sorted(vals, reverse=True))

    def test_weakest_question_type_carries_more_weight(self):
        base = datetime.datetime.now() - datetime.timedelta(days=2)
        logs = []
        # englishtoltl: all wrong (weak); mc: all right (mastered).
        for i in range(8):
            logs.append(FakeLog(base + datetime.timedelta(minutes=i * 10),
                                ExerciseBuilder.ENGLISHTOLTL, False))
        for i in range(8):
            logs.append(FakeLog(base + datetime.timedelta(minutes=100 + i * 10),
                                ExerciseBuilder.TRACESATMC, True))
        weights = ExerciseBuilder(logs).get_profile_snapshot()['question_type_weights']
        self.assertGreater(weights[ExerciseBuilder.ENGLISHTOLTL],
                           weights[ExerciseBuilder.TRACESATMC])

    def test_complexity_reported_and_clamped(self):
        # A persisted out-of-range complexity is clamped by __init__.
        snap = ExerciseBuilder([], complexity=99).get_profile_snapshot()
        self.assertEqual(snap['complexity'], ExerciseBuilder.COMPLEXITY_MAX)
        self.assertEqual(snap['complexity_band'], "Advanced")


if __name__ == '__main__':
    unittest.main()
