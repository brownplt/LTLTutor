import unittest
import sys
import os

# Add the src directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot module to avoid import error
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from spotutils import weighted_trace_choice


class TestWeightedTraceChoice(unittest.TestCase):
    """Test cases for weighted trace selection that slightly prefers shorter traces."""

    def test_single_trace_returns_that_trace(self):
        """When there's only one trace, it should be returned."""
        traces = ["a; cycle{1}"]
        result = weighted_trace_choice(traces)
        self.assertEqual(result, "a; cycle{1}")

    def test_empty_list_raises_error(self):
        """Empty list should raise an error."""
        with self.assertRaises(ValueError):
            weighted_trace_choice([])

    def test_returns_element_from_list(self):
        """Result should always be an element from the input list."""
        traces = [
            "cycle{!a | b}",
            "a & !b; b; cycle{!a | b}",
            "!a | b; a & !b; b; cycle{!a | b}",
        ]
        for _ in range(100):
            result = weighted_trace_choice(traces)
            self.assertIn(result, traces)

    def test_shorter_traces_selected_more_often(self):
        """Shorter traces should be selected more frequently than longer ones."""
        # Create traces with significantly different lengths
        short_trace = "a"  # length 1
        long_trace = "a; b; c; d; e; f; g; h; i; j; k; l; m; n; o; p; q; r; s; t"  # length 59
        traces = [short_trace, long_trace]
        
        # Run many trials
        short_count = 0
        long_count = 0
        trials = 1000
        
        for _ in range(trials):
            result = weighted_trace_choice(traces)
            if result == short_trace:
                short_count += 1
            else:
                long_count += 1
        
        # Short trace should be selected more often due to weighting
        # With inverse length weighting:
        # short weight = 1/(1+1) = 0.5
        # long weight = 1/(1+59) = 0.0167
        # So short should be ~97% of selections
        self.assertGreater(short_count, long_count,
            f"Short trace should be selected more often. Got short={short_count}, long={long_count}")
        
        # Short should be selected at least 80% of the time with these lengths
        self.assertGreater(short_count / trials, 0.8,
            f"Short trace should be selected at least 80% of the time. Got {short_count/trials:.2%}")

    def test_long_traces_still_possible(self):
        """Long traces should still be selectable (not excluded)."""
        # Create traces with different lengths
        traces = [
            "a",  # Very short
            "a; b; c; d; e; f; g; h",  # Medium
            "a; b; c; d; e; f; g; h; i; j; k; l",  # Long
        ]
        
        # With weighted selection, even the longest trace should appear sometimes
        # Run enough trials to have a good chance of seeing all traces
        results = set()
        for _ in range(500):
            results.add(weighted_trace_choice(traces))
            if len(results) == len(traces):
                break
        
        # All traces should have been selected at least once
        self.assertEqual(len(results), len(traces),
            f"All traces should be selectable. Got {results}")

    def test_moderate_length_difference(self):
        """Test with traces of moderate length difference (more realistic)."""
        traces = [
            "cycle{!a | b}",  # len 13
            "a & !b; b; cycle{!a | b}",  # len 24
            "!a | b; a & !b; b; cycle{!a | b}",  # len 32
        ]
        
        # Run many trials
        counts = {t: 0 for t in traces}
        trials = 1000
        
        for _ in range(trials):
            result = weighted_trace_choice(traces)
            counts[result] += 1
        
        # Shorter trace should be most common
        shortest = traces[0]
        medium = traces[1]
        longest = traces[2]
        
        self.assertGreater(counts[shortest], counts[medium],
            f"Shortest should be more common than medium. Got {counts[shortest]} vs {counts[medium]}")
        self.assertGreater(counts[medium], counts[longest],
            f"Medium should be more common than longest. Got {counts[medium]} vs {counts[longest]}")

    def test_identical_lengths_equal_probability(self):
        """Traces with identical lengths should have roughly equal probability."""
        traces = ["abc", "def", "ghi"]  # All length 3
        
        counts = {t: 0 for t in traces}
        trials = 1000
        
        for _ in range(trials):
            result = weighted_trace_choice(traces)
            counts[result] += 1
        
        # Each trace should be selected roughly 1/3 of the time
        # Allow for some statistical variance (within 10% of expected)
        expected = trials / 3
        for trace, count in counts.items():
            self.assertAlmostEqual(count / trials, 1/3, delta=0.1,
                msg=f"Trace '{trace}' selected {count} times, expected ~{expected:.0f}")


if __name__ == "__main__":
    unittest.main()
