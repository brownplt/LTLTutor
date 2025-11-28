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
from codebook import MisconceptionCode


class MockStudentLog:
    """Mock class to simulate student response logs."""
    def __init__(self, misconception, timestamp):
        self.misconception = misconception
        self.timestamp = timestamp


class TestRegressionModel(unittest.TestCase):
    """Test cases for the improved misconception regression model."""

    def test_empty_logs_returns_default_weights(self):
        """With no logs, all misconceptions should have default weight."""
        builder = ExerciseBuilder([])
        concept_history = builder.aggregateLogs()
        weights = builder.calculate_misconception_weights(concept_history)
        
        # All weights should be around the default (0.5)
        for weight in weights.values():
            self.assertAlmostEqual(weight, 0.5, delta=0.1)

    def test_recent_misconceptions_weighted_higher(self):
        """Recent misconceptions should have higher weights than older ones."""
        now = datetime.datetime.now()
        
        # Create logs with recent misconception (ImplicitG) and older one (ImplicitF)
        recent_log = MockStudentLog(
            str(MisconceptionCode.ImplicitG), 
            now - datetime.timedelta(hours=1)
        )
        older_log = MockStudentLog(
            str(MisconceptionCode.ImplicitF), 
            now - datetime.timedelta(days=7)
        )
        
        builder = ExerciseBuilder([recent_log, older_log])
        concept_history = builder.aggregateLogs()
        weights = builder.calculate_misconception_weights(concept_history)
        
        # Recent misconception should have higher weight
        self.assertGreater(
            weights[str(MisconceptionCode.ImplicitG)],
            weights[str(MisconceptionCode.ImplicitF)]
        )

    def test_frequent_misconceptions_weighted_higher(self):
        """More frequent misconceptions should have higher weights."""
        now = datetime.datetime.now()
        
        # Create multiple logs for frequent misconception
        logs = []
        for i in range(5):
            logs.append(MockStudentLog(
                str(MisconceptionCode.Precedence),
                now - datetime.timedelta(hours=i+1)
            ))
        
        # Single log for infrequent misconception
        logs.append(MockStudentLog(
            str(MisconceptionCode.WeakU),
            now - datetime.timedelta(hours=1)
        ))
        
        builder = ExerciseBuilder(logs)
        concept_history = builder.aggregateLogs()
        weights = builder.calculate_misconception_weights(concept_history)
        
        # Frequent misconception should have higher weight
        self.assertGreater(
            weights[str(MisconceptionCode.Precedence)],
            weights[str(MisconceptionCode.WeakU)]
        )

    def test_drilling_boost_for_persistent_misconceptions(self):
        """Persistent recent misconceptions should get drilling boost."""
        now = datetime.datetime.now()
        
        # Create many recent logs to trigger drilling
        drilling_logs = []
        for i in range(5):
            drilling_logs.append(MockStudentLog(
                str(MisconceptionCode.ExclusiveU),
                now - datetime.timedelta(hours=i+1)
            ))
        
        builder_with_drilling = ExerciseBuilder(drilling_logs)
        concept_history_drilling = builder_with_drilling.aggregateLogs()
        weights_drilling = builder_with_drilling.calculate_misconception_weights(
            concept_history_drilling
        )
        
        # Single recent log (no drilling)
        single_log = [MockStudentLog(
            str(MisconceptionCode.ExclusiveU),
            now - datetime.timedelta(hours=1)
        )]
        
        builder_single = ExerciseBuilder(single_log)
        concept_history_single = builder_single.aggregateLogs()
        weights_single = builder_single.calculate_misconception_weights(
            concept_history_single
        )
        
        # Drilling case should have higher weight
        self.assertGreater(
            weights_drilling[str(MisconceptionCode.ExclusiveU)],
            weights_single[str(MisconceptionCode.ExclusiveU)]
        )

    def test_weights_bounded_between_zero_and_one(self):
        """All weights should be bounded between 0 and 1 (sigmoid)."""
        now = datetime.datetime.now()
        
        # Create many logs to test bounds
        logs = []
        for i in range(50):
            logs.append(MockStudentLog(
                str(MisconceptionCode.BadStateIndex),
                now - datetime.timedelta(hours=i)
            ))
        
        builder = ExerciseBuilder(logs)
        concept_history = builder.aggregateLogs()
        weights = builder.calculate_misconception_weights(concept_history)
        
        for weight in weights.values():
            self.assertGreaterEqual(weight, 0)
            self.assertLessEqual(weight, 1)

    def test_trend_calculation_worsening(self):
        """Test that worsening trends are detected."""
        now = datetime.datetime.now()
        builder = ExerciseBuilder([])
        
        # Create entries showing worsening trend (more recent = more frequent)
        entries = [
            (now - datetime.timedelta(hours=72), 1),  # Older: low frequency
            (now - datetime.timedelta(hours=24), 3),  # Recent: higher frequency
        ]
        
        trend_score, has_recent_data = builder._calculate_trend(entries, now)
        
        # Trend should be positive (worsening)
        self.assertGreater(trend_score, 0)
        self.assertTrue(has_recent_data)

    def test_trend_calculation_improving(self):
        """Test that improving trends are detected."""
        now = datetime.datetime.now()
        builder = ExerciseBuilder([])
        
        # Create entries showing improving trend (more recent = less frequent)
        entries = [
            (now - datetime.timedelta(hours=72), 5),  # Older: high frequency
            (now - datetime.timedelta(hours=24), 1),  # Recent: lower frequency
        ]
        
        trend_score, has_recent_data = builder._calculate_trend(entries, now)
        
        # Trend should be negative (improving)
        self.assertLess(trend_score, 0)
        self.assertTrue(has_recent_data)

    def test_trend_calculation_insufficient_data(self):
        """Test that insufficient data returns neutral trend."""
        now = datetime.datetime.now()
        builder = ExerciseBuilder([])
        
        # Single entry - returns slight positive (new misconception)
        entries = [(now - datetime.timedelta(hours=24), 2)]
        
        trend_score, has_recent_data = builder._calculate_trend(entries, now)
        
        # Should return 0.25 for new misconception with recent data
        self.assertEqual(trend_score, 0.25)
        self.assertTrue(has_recent_data)
    
    def test_trend_calculation_no_entries(self):
        """Test that no entries returns zero trend with no recent data."""
        now = datetime.datetime.now()
        builder = ExerciseBuilder([])
        
        entries = []
        
        trend_score, has_recent_data = builder._calculate_trend(entries, now)
        
        # Should return 0 with no recent data
        self.assertEqual(trend_score, 0)
        self.assertFalse(has_recent_data)
    
    def test_trend_calculation_historical_data_only(self):
        """Test that historical data (older than 96h) still calculates trends."""
        now = datetime.datetime.now()
        builder = ExerciseBuilder([])
        
        # Create entries all older than 96 hours
        entries = [
            (now - datetime.timedelta(hours=200), 1),  # Very old: low frequency
            (now - datetime.timedelta(hours=150), 3),  # Less old: higher frequency
        ]
        
        trend_score, has_recent_data = builder._calculate_trend(entries, now)
        
        # Should still calculate trend based on relative comparison
        self.assertGreater(trend_score, 0)  # Worsening over historical period
        self.assertFalse(has_recent_data)  # No recent data flag

    def test_exponential_decay_over_time(self):
        """Test that weights decay exponentially over time."""
        now = datetime.datetime.now()
        
        # Create log from 24 hours ago
        log_24h = [MockStudentLog(
            str(MisconceptionCode.ImplicitG),
            now - datetime.timedelta(hours=24)
        )]
        
        # Create log from 48 hours ago
        log_48h = [MockStudentLog(
            str(MisconceptionCode.ImplicitG),
            now - datetime.timedelta(hours=48)
        )]
        
        builder_24h = ExerciseBuilder(log_24h)
        concept_history_24h = builder_24h.aggregateLogs()
        weights_24h = builder_24h.calculate_misconception_weights(concept_history_24h)
        
        builder_48h = ExerciseBuilder(log_48h)
        concept_history_48h = builder_48h.aggregateLogs()
        weights_48h = builder_48h.calculate_misconception_weights(concept_history_48h)
        
        # 24h should have higher weight than 48h
        self.assertGreater(
            weights_24h[str(MisconceptionCode.ImplicitG)],
            weights_48h[str(MisconceptionCode.ImplicitG)]
        )


class TestAggregateLogsIntegration(unittest.TestCase):
    """Integration tests for log aggregation with the new model."""

    def test_aggregate_logs_empty(self):
        """Empty logs should produce empty concept history."""
        builder = ExerciseBuilder([])
        concept_history = builder.aggregateLogs()
        
        # Should have all misconception codes but with empty lists
        for code in MisconceptionCode:
            self.assertIn(str(code), concept_history)

    def test_aggregate_logs_buckets_by_hour(self):
        """Logs should be aggregated into hourly buckets."""
        now = datetime.datetime.now()
        base_time = now.replace(minute=0, second=0, microsecond=0)
        
        # Create two logs in same hour
        logs = [
            MockStudentLog(str(MisconceptionCode.Precedence), base_time + datetime.timedelta(minutes=10)),
            MockStudentLog(str(MisconceptionCode.Precedence), base_time + datetime.timedelta(minutes=30)),
        ]
        
        builder = ExerciseBuilder(logs)
        concept_history = builder.aggregateLogs()
        
        # Should have one bucket with frequency 2
        precedence_history = concept_history[str(MisconceptionCode.Precedence)]
        self.assertEqual(len(precedence_history), 1)
        self.assertEqual(precedence_history[0][1], 2)


if __name__ == "__main__":
    unittest.main()
