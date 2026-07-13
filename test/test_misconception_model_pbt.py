import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

import misconceptionmodel

try:
    from hypothesis import given, settings, strategies as st
    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - local minimal environment
    HAS_HYPOTHESIS = False
    st = None


def make_events(observations):
    start = datetime.datetime(2026, 7, 12, 12, 0, 0)
    return [
        {
            'timestamp': start + datetime.timedelta(minutes=index),
            'observation': observation,
            'evidence_strength': strength,
        }
        for index, (observation, strength) in enumerate(observations)
    ]


@unittest.skipUnless(HAS_HYPOTHESIS, 'hypothesis not installed')
class TestMisconceptionModelProperties(unittest.TestCase):
    if HAS_HYPOTHESIS:
        sequences = st.lists(
            st.tuples(
                st.sampled_from(['positive', 'negative', 'ambiguous']),
                st.floats(min_value=0, max_value=1, allow_nan=False, allow_infinity=False),
            ),
            max_size=100,
        )

        @settings(max_examples=200, deadline=None)
        @given(sequences)
        def test_score_always_stays_within_documented_bounds(self, observations):
            events = make_events(observations)
            now = events[-1]['timestamp'] if events else datetime.datetime(2026, 7, 12)
            score = misconceptionmodel.calculate_evidence_score(events, now=now)
            self.assertGreaterEqual(score, misconceptionmodel.MIN_SCORE)
            self.assertLessEqual(score, misconceptionmodel.MAX_SCORE)

        @settings(max_examples=100, deadline=None)
        @given(sequences)
        def test_new_positive_cannot_lower_score(self, observations):
            events = make_events(observations)
            timestamp = events[-1]['timestamp'] if events else datetime.datetime(2026, 7, 12)
            before = misconceptionmodel.calculate_evidence_score(events, now=timestamp)
            after = misconceptionmodel.calculate_evidence_score(
                events + [{'timestamp': timestamp, 'observation': 'positive', 'evidence_strength': 1.0}],
                now=timestamp,
            )
            self.assertGreaterEqual(after, before)

        @settings(max_examples=100, deadline=None)
        @given(sequences)
        def test_new_negative_cannot_raise_score(self, observations):
            events = make_events(observations)
            timestamp = events[-1]['timestamp'] if events else datetime.datetime(2026, 7, 12)
            before = misconceptionmodel.calculate_evidence_score(events, now=timestamp)
            after = misconceptionmodel.calculate_evidence_score(
                events + [{'timestamp': timestamp, 'observation': 'negative', 'evidence_strength': 1.0}],
                now=timestamp,
            )
            self.assertLessEqual(after, before)


if __name__ == '__main__':
    unittest.main()
