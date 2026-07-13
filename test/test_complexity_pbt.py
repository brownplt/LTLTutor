"""
Property-based tests for the adaptive-complexity model (ExerciseBuilder).

These exercise update_complexity() and its supporting log-deduplication across
many randomly generated student profiles, checking invariants that must hold
for *every* history rather than a handful of hand-picked cases:

  - complexity always stays within [MIN, MAX];
  - it moves at most one step per call;
  - it does not move until there are enough recent answers;
  - the step direction matches the recent accuracy, regardless of how
    correct_answer is represented (bool or string);
  - repeated calls converge to the ceiling for a consistently strong student
    and to the floor for a consistently weak one;
  - duplicate per-misconception rows for one wrong answer count once.

Uses Hypothesis if it is installed (see test/requirements.txt); if not, the
whole module is skipped so the rest of the suite still runs.
"""

import unittest
import sys
import os
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Mock spot the same way the rest of the suite does.
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from exercisebuilder import ExerciseBuilder

try:
    from hypothesis import given, settings, strategies as st, HealthCheck
    HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - exercised only where hypothesis is absent
    HAS_HYPOTHESIS = False

    # Provide no-op stand-ins so the class below still *defines* (its decorators
    # and class-scope strategy references run at import time); skipUnless then
    # skips every test. This keeps the suite runnable without hypothesis.
    def given(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    def settings(*args, **kwargs):
        def decorator(func):
            return func
        return decorator

    class _StrategyStub:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    st = _StrategyStub()

    class HealthCheck:
        too_slow = None


MIN = ExerciseBuilder.COMPLEXITY_MIN
MAX = ExerciseBuilder.COMPLEXITY_MAX
WINDOW = ExerciseBuilder.COMPLEXITY_WINDOW
MIN_ANSWERS = ExerciseBuilder.COMPLEXITY_MIN_ANSWERS
UP = ExerciseBuilder.COMPLEXITY_STEP_UP_ACCURACY
DOWN = ExerciseBuilder.COMPLEXITY_STEP_DOWN_ACCURACY

# A fixed base time keeps the tests deterministic. Nothing on the
# update_complexity path reads the wall clock.
BASE = datetime.datetime(2026, 1, 1, 12, 0, 0)

# Representations of a correct / incorrect answer that appear in real rows.
CORRECT_REPRS = ['True', 'true', 'TRUE', True]
INCORRECT_REPRS = ['False', 'false', '', False, None]


class FakeLog:
    def __init__(self, timestamp, question_type, correct_answer, question_text):
        self.timestamp = timestamp
        self.question_type = question_type
        self.correct_answer = correct_answer
        self.misconception = ''
        self.question_text = question_text


def build_distinct_logs(answers):
    """One log per answer, unique question_text and minute-spaced timestamps so
    _distinct_answers keeps them all. `answers` is a list of (is_correct, repr)."""
    logs = []
    for i, (_is_correct, rep) in enumerate(answers):
        logs.append(FakeLog(BASE + datetime.timedelta(minutes=i),
                            ExerciseBuilder.TRACESATMC, rep, f"q{i}"))
    return logs


def expected_complexity(correctness_bools, start):
    """Oracle re-implementation of the update rule, used to check equivalence."""
    c = max(MIN, min(MAX, start))
    recent = correctness_bools[-WINDOW:]
    if len(recent) >= MIN_ANSWERS:
        accuracy = sum(1 for x in recent if x) / len(recent)
        if accuracy >= UP:
            c += 1
        elif accuracy <= DOWN:
            c -= 1
    return max(MIN, min(MAX, c))


@unittest.skipUnless(HAS_HYPOTHESIS, "hypothesis not installed")
class TestComplexityProperties(unittest.TestCase):

    # Each answer is a (correctness_bool, stored_representation) pair, so the
    # coercion of correct_answer is folded into every property below.
    answers = st.lists(
        st.one_of(
            st.tuples(st.just(True), st.sampled_from(CORRECT_REPRS)),
            st.tuples(st.just(False), st.sampled_from(INCORRECT_REPRS)),
        ),
        max_size=40,
    )

    @settings(max_examples=300, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(answers=answers, start=st.integers(min_value=-20, max_value=40))
    def test_matches_oracle_and_stays_in_bounds(self, answers, start):
        """The single strongest property: for any history and any (even
        out-of-range) starting complexity, update_complexity equals the oracle
        and lands within [MIN, MAX]. Subsumes clamping, the min-answers gate,
        the accuracy thresholds, and representation coercion."""
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        result = builder.update_complexity()
        bools = [c for c, _ in answers]
        self.assertEqual(result, expected_complexity(bools, start))
        self.assertGreaterEqual(result, MIN)
        self.assertLessEqual(result, MAX)
        self.assertEqual(result, builder.complexity)

    @settings(max_examples=200, deadline=None)
    @given(answers=answers, start=st.integers(min_value=MIN, max_value=MAX))
    def test_moves_at_most_one_step(self, answers, start):
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        before = builder.complexity  # already in range
        after = builder.update_complexity()
        self.assertLessEqual(abs(after - before), 1)

    @settings(max_examples=200, deadline=None)
    @given(
        answers=st.lists(
            st.one_of(
                st.tuples(st.just(True), st.sampled_from(CORRECT_REPRS)),
                st.tuples(st.just(False), st.sampled_from(INCORRECT_REPRS)),
            ),
            max_size=MIN_ANSWERS - 1,  # fewer distinct answers than the gate
        ),
        start=st.integers(min_value=MIN, max_value=MAX),
    )
    def test_no_movement_below_min_answers(self, answers, start):
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        before = builder.complexity
        after = builder.update_complexity()
        self.assertEqual(after, before)

    @settings(max_examples=100, deadline=None)
    @given(start=st.integers(min_value=MIN, max_value=MAX - 1),
           n=st.integers(min_value=MIN_ANSWERS, max_value=25))
    def test_strong_history_steps_up(self, start, n):
        answers = [(True, True)] * n
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        self.assertEqual(builder.update_complexity(), start + 1)

    @settings(max_examples=100, deadline=None)
    @given(start=st.integers(min_value=MIN + 1, max_value=MAX),
           n=st.integers(min_value=MIN_ANSWERS, max_value=25))
    def test_weak_history_steps_down(self, start, n):
        answers = [(False, False)] * n
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        self.assertEqual(builder.update_complexity(), start - 1)

    @settings(max_examples=100, deadline=None)
    @given(start=st.integers(min_value=MIN, max_value=MAX),
           k=st.integers(min_value=5, max_value=7))
    def test_middling_accuracy_holds(self, start, k):
        # A full window of exactly 10 with k correct -> accuracy in {.5,.6,.7},
        # strictly between the down (0.45) and up (0.8) thresholds.
        answers = [(True, True)] * k + [(False, False)] * (10 - k)
        builder = ExerciseBuilder(build_distinct_logs(answers), complexity=start)
        before = builder.complexity
        self.assertEqual(builder.update_complexity(), before)

    @settings(max_examples=50, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(start=st.integers(min_value=MIN, max_value=MAX))
    def test_repeated_updates_converge_to_ceiling_for_strong_student(self, start):
        # Mirror the request loop: rebuild the builder each exercise with the
        # persisted complexity, appending five correct answers each time.
        complexity = start
        logs = []
        for ex in range(30):
            builder = ExerciseBuilder(list(logs), complexity=complexity)
            complexity = builder.update_complexity()
            for j in range(5):
                idx = ex * 5 + j
                logs.append(FakeLog(BASE + datetime.timedelta(minutes=idx),
                                    ExerciseBuilder.TRACESATMC, True, f"q{idx}"))
        self.assertEqual(complexity, MAX)

    @settings(max_examples=50, deadline=None,
              suppress_health_check=[HealthCheck.too_slow])
    @given(start=st.integers(min_value=MIN, max_value=MAX))
    def test_repeated_updates_converge_to_floor_for_weak_student(self, start):
        complexity = start
        logs = []
        for ex in range(30):
            builder = ExerciseBuilder(list(logs), complexity=complexity)
            complexity = builder.update_complexity()
            for j in range(5):
                idx = ex * 5 + j
                logs.append(FakeLog(BASE + datetime.timedelta(minutes=idx),
                                    ExerciseBuilder.TRACESATMC, False, f"q{idx}"))
        self.assertEqual(complexity, MIN)

    @settings(max_examples=100, deadline=None)
    @given(dupes=st.integers(min_value=1, max_value=5))
    def test_duplicate_misconception_rows_count_once(self, dupes):
        """One wrong answer logged once per misconception (same question_text,
        sub-5-second timestamps) must count as a single wrong answer, not
        `dupes` of them — otherwise accuracy is understated."""
        logs = []
        # The duplicated wrong answer: same question_text, all within <5s.
        for d in range(dupes):
            logs.append(FakeLog(BASE + datetime.timedelta(seconds=d),
                                ExerciseBuilder.TRACESATMC, False, "wrong"))
        # Nine clearly-correct, well-spaced, distinct answers.
        for i in range(9):
            logs.append(FakeLog(BASE + datetime.timedelta(minutes=5 * (i + 1)),
                                ExerciseBuilder.TRACESATMC, True, f"c{i}"))
        builder = ExerciseBuilder(logs, complexity=5)
        # Deduped: 1 wrong + 9 correct = 10 answers, accuracy 0.9 >= 0.8 -> up.
        self.assertEqual(builder.update_complexity(), 6)


if __name__ == '__main__':
    unittest.main()
