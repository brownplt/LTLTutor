import unittest
import sys
import os
import random

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from exercisebuilder import ExerciseBuilder


class StubBuilder(ExerciseBuilder):
    """ExerciseBuilder with fixed misconception weights, so distractor
    sampling can be tested without SPOT or a database."""

    def __init__(self, weights):
        super().__init__([])
        self._fixed_weights = weights

    def aggregateLogs(self, bucketsizeinhours=1):
        return {}

    def calculate_misconception_weights(self, concept_history):
        return self._fixed_weights


def opt(*codes):
    return {"option": "+".join(codes), "isCorrect": False, "misconceptions": list(codes)}


class TestSampleMisconceptionOptions(unittest.TestCase):

    def test_returns_unchanged_when_within_budget(self):
        builder = StubBuilder({})
        options = [opt("A"), opt("B")]
        self.assertIs(builder._sample_misconception_options(options, 4), options)

    def test_reduces_to_budget_no_dupes(self):
        builder = StubBuilder({c: 0.5 for c in "ABCDEFG"})
        options = [opt(c) for c in "ABCDEFG"]
        random.seed(1)
        result = builder._sample_misconception_options(options, 4)
        self.assertEqual(len(result), 4)
        # every result came from the input, no duplicates
        keys = [o["option"] for o in result]
        self.assertEqual(len(set(keys)), 4)
        for o in result:
            self.assertIn(o, options)

    def test_high_weight_misconception_favored(self):
        builder = StubBuilder({"HIGH": 0.95, "LOW": 0.05,
                               "M1": 0.5, "M2": 0.5, "M3": 0.5})
        options = [opt("HIGH"), opt("LOW"), opt("M1"), opt("M2"), opt("M3")]
        high_seen = low_seen = 0
        for s in range(400):
            random.seed(s)
            result = builder._sample_misconception_options(options, 3)
            keys = {o["option"] for o in result}
            high_seen += "HIGH" in keys
            low_seen += "LOW" in keys
        self.assertGreater(high_seen, low_seen)

    def test_floor_keeps_low_weight_in_rotation(self):
        """A weight-0 misconception must still appear sometimes."""
        builder = StubBuilder({"HIGH": 1.0, "ZERO": 0.0,
                               "M1": 0.9, "M2": 0.9, "M3": 0.9})
        options = [opt("HIGH"), opt("ZERO"), opt("M1"), opt("M2"), opt("M3")]
        zero_seen = 0
        for s in range(400):
            random.seed(s)
            result = builder._sample_misconception_options(options, 3)
            if any(o["option"] == "ZERO" for o in result):
                zero_seen += 1
        self.assertGreater(zero_seen, 0)

    def test_merged_option_uses_max_weight(self):
        builder = StubBuilder({"LOW": 0.05, "HIGH": 0.95, "M1": 0.5, "M2": 0.5})
        merged = opt("LOW", "HIGH")   # carries both codes
        plain_low = opt("LOWONLY")
        builder._fixed_weights["LOWONLY"] = 0.05
        options = [merged, plain_low, opt("M1"), opt("M2")]
        merged_seen = plain_seen = 0
        for s in range(400):
            random.seed(s)
            result = builder._sample_misconception_options(options, 2)
            keys = {o["option"] for o in result}
            merged_seen += merged["option"] in keys
            plain_seen += "LOWONLY" in keys
        # The merged option should win more often thanks to its HIGH code.
        self.assertGreater(merged_seen, plain_seen)


class TestWeightedSampleWithoutReplacement(unittest.TestCase):

    def test_returns_k_distinct(self):
        builder = ExerciseBuilder([])
        items = list("ABCDEFG")
        random.seed(3)
        result = builder._weighted_sample_without_replacement(items, lambda x: 1.0, 3)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(set(result)), 3)

    def test_returns_all_when_k_exceeds_pool(self):
        builder = ExerciseBuilder([])
        items = ["A", "B"]
        result = builder._weighted_sample_without_replacement(items, lambda x: 1.0, 5)
        self.assertEqual(sorted(result), ["A", "B"])

    def test_zero_weight_items_handled(self):
        builder = ExerciseBuilder([])
        items = ["A", "B", "C"]
        random.seed(0)
        result = builder._weighted_sample_without_replacement(items, lambda x: 0.0, 2)
        self.assertEqual(len(result), 2)


if __name__ == '__main__':
    unittest.main()
