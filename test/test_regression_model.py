import datetime
import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.modules['spot'] = MagicMock()

import misconceptionmodel
from codebook import MisconceptionCode
from exercisebuilder import ExerciseBuilder


def event(code, observation, timestamp, strength=1.0):
    return SimpleNamespace(
        misconception=str(code),
        observation=observation,
        timestamp=timestamp,
        evidence_strength=strength,
    )


class TestOptionAwareEvidenceModel(unittest.TestCase):
    def setUp(self):
        self.now = datetime.datetime(2026, 7, 12, 12, 0, 0)
        self.code = MisconceptionCode.ImplicitG

    def score(self, events, now=None):
        builder = ExerciseBuilder([], misconception_opportunities=events)
        history = builder.aggregate_misconception_evidence()
        return builder.calculate_misconception_weights(
            history, now=now or self.now
        )[str(self.code)]

    def test_no_opportunities_returns_uncertain_prior(self):
        builder = ExerciseBuilder([])
        scores = builder.calculate_misconception_weights(
            builder.aggregate_misconception_evidence(), now=self.now
        )
        self.assertNotIn(str(MisconceptionCode.Syntactic), scores)
        for score in scores.values():
            self.assertEqual(score, misconceptionmodel.PRIOR_SCORE)

    def test_repeated_positive_observations_increase_monotonically(self):
        events = []
        scores = []
        for index in range(5):
            events.append(event(self.code, 'positive', self.now + datetime.timedelta(minutes=index)))
            scores.append(self.score(events, now=events[-1].timestamp))
        self.assertEqual(scores, sorted(scores))
        self.assertGreater(scores[-1], scores[0])

    def test_repeated_negative_observations_decrease_monotonically(self):
        events = []
        scores = []
        for index in range(5):
            events.append(event(self.code, 'negative', self.now + datetime.timedelta(minutes=index)))
            scores.append(self.score(events, now=events[-1].timestamp))
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertLess(scores[-1], scores[0])

    def test_ambiguous_opportunity_does_not_move_score(self):
        ambiguous = [event(self.code, 'ambiguous', self.now)]
        self.assertEqual(self.score(ambiguous), misconceptionmodel.PRIOR_SCORE)

    def test_unrelated_misconception_does_not_move_score(self):
        events = [event(MisconceptionCode.ImplicitF, 'positive', self.now)]
        self.assertEqual(self.score(events), misconceptionmodel.PRIOR_SCORE)

    def test_merged_distractor_supplies_weaker_positive_evidence(self):
        direct = self.score([event(self.code, 'positive', self.now, 1.0)])
        merged = self.score([event(self.code, 'positive', self.now, 0.5)])
        self.assertGreater(direct, merged)
        self.assertGreater(merged, misconceptionmodel.PRIOR_SCORE)

    def test_single_observation_never_creates_certainty(self):
        positive = self.score([event(self.code, 'positive', self.now)])
        negative = self.score([event(self.code, 'negative', self.now)])
        self.assertLess(positive, misconceptionmodel.MAX_SCORE)
        self.assertGreater(negative, misconceptionmodel.MIN_SCORE)

    def test_time_alone_decays_positive_evidence_toward_uncertainty(self):
        events = [event(self.code, 'positive', self.now)]
        recent = self.score(events, now=self.now)
        stale = self.score(events, now=self.now + datetime.timedelta(days=120))
        self.assertGreater(recent, stale)
        self.assertGreater(stale, misconceptionmodel.PRIOR_SCORE)

    def test_time_alone_decays_negative_evidence_toward_uncertainty(self):
        events = [event(self.code, 'negative', self.now)]
        recent = self.score(events, now=self.now)
        stale = self.score(events, now=self.now + datetime.timedelta(days=120))
        self.assertLess(recent, stale)
        self.assertLess(stale, misconceptionmodel.PRIOR_SCORE)

    def test_scores_remain_bounded_under_long_sequences(self):
        positives = [event(self.code, 'positive', self.now) for _ in range(100)]
        negatives = [event(self.code, 'negative', self.now) for _ in range(100)]
        self.assertGreaterEqual(self.score(positives), misconceptionmodel.MIN_SCORE)
        self.assertLessEqual(self.score(positives), misconceptionmodel.MAX_SCORE)
        self.assertGreaterEqual(self.score(negatives), misconceptionmodel.MIN_SCORE)
        self.assertLessEqual(self.score(negatives), misconceptionmodel.MAX_SCORE)


if __name__ == '__main__':
    unittest.main()
