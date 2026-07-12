"""
Quantify the behavioral difference between the pre-2.0.0 exercise-selection
policy and the current one, without needing student data.

Old policy (pre-2.0.0, reconstructed here):
  - complexity: effectively constant at 5 for every student, forever.
    (ExerciseBuilder bumped self.complexity in-memory, but the value was
    never written to generated_exercise.complexity, so getComplexity always
    returned None and each request started from the default.)
  - question type: uniform random.choice over the three types.

New policy (2.0.0):
  - complexity: persisted per user; one step up when recent accuracy >= 80%,
    one step down when <= 45%, clamped to [3, 12].
  - question type: drawn weighted by Laplace-smoothed per-type error rate,
    with a 15% exploration floor.

We simulate archetype students through both policies and report:
  - complexity trajectories (the old one is flat by construction)
  - share of questions served from the student's weakest type
  - how quickly the served difficulty reacts to a performance change

Run from the repo root:  python3 experiments/policy_comparison.py
No SPOT needed (the spot module is mocked, as in the unit tests).
"""

import datetime
import os
import random
import sys
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.modules.setdefault('spot', MagicMock())

from exercisebuilder import ExerciseBuilder  # noqa: E402

RNG_SEED = 7
EXERCISES = 30
QUESTIONS_PER_EXERCISE = 5


class SimLog:
    """Minimal stand-in for a student_responses row."""

    def __init__(self, timestamp, question_text, question_type, correct_answer):
        self.timestamp = timestamp
        self.question_text = question_text
        self.question_type = question_type
        self.correct_answer = correct_answer
        self.misconception = ""


class Archetype:
    """A simulated student: per-type base accuracy, optionally drifting."""

    def __init__(self, name, base_accuracy, drift_per_exercise=0.0):
        self.name = name
        # base_accuracy: dict qtype -> probability of a correct answer at complexity 5
        self.base_accuracy = base_accuracy
        self.drift_per_exercise = drift_per_exercise

    def p_correct(self, qtype, complexity, exercise_index):
        p = self.base_accuracy[qtype] + self.drift_per_exercise * exercise_index
        # Harder exercises are harder: each complexity step above 5 costs 3 points
        p -= 0.03 * (complexity - 5)
        return min(0.98, max(0.05, p))


QT = ExerciseBuilder.QUESTION_TYPES
UNIFORM = {q: 1.0 / len(QT) for q in QT}


def simulate(archetype, policy, rng):
    """
    Run one student through EXERCISES generated exercises under a policy
    ('old' or 'new'). Returns (complexity_trajectory, served_type_counts,
    per_exercise_accuracy).
    """
    logs = []
    now = datetime.datetime.now() - datetime.timedelta(days=1)
    persisted_complexity = None  # what generated_exercise.complexity holds
    complexity_trajectory = []
    served = {q: 0 for q in QT}
    accuracy_per_exercise = []

    for ex in range(EXERCISES):
        if policy == 'old':
            # getComplexity always returned None -> default 5, every time
            builder = ExerciseBuilder(list(logs))
            builder.complexity = 5
            complexity = 5
            weights = UNIFORM
        else:
            if persisted_complexity is None:
                builder = ExerciseBuilder(list(logs))
            else:
                builder = ExerciseBuilder(list(logs), complexity=persisted_complexity)
            complexity = builder.update_complexity()
            persisted_complexity = complexity
            weights = builder.calculate_question_type_weights()

        complexity_trajectory.append(complexity)

        correct_count = 0
        for q in range(QUESTIONS_PER_EXERCISE):
            qtype = rng.choices(QT, weights=[weights[t] for t in QT], k=1)[0]
            served[qtype] += 1
            p = archetype.p_correct(qtype, complexity, ex)
            correct = rng.random() < p
            correct_count += int(correct)
            now += datetime.timedelta(minutes=3)
            logs.append(SimLog(now, f"q-{ex}-{q}", qtype, correct))

        accuracy_per_exercise.append(correct_count / QUESTIONS_PER_EXERCISE)

    return complexity_trajectory, served, accuracy_per_exercise


def weakest_type(archetype):
    return min(archetype.base_accuracy, key=archetype.base_accuracy.get)


def fmt_traj(traj):
    return f"start {traj[0]}, end {traj[-1]}, min {min(traj)}, max {max(traj)}"


def main():
    archetypes = [
        Archetype("strong (90% everywhere)",
                  {q: 0.9 for q in QT}),
        Archetype("struggling (30% everywhere)",
                  {q: 0.3 for q in QT}),
        Archetype("improving (40% -> 90%)",
                  {q: 0.4 for q in QT}, drift_per_exercise=0.02),
        Archetype("yn-weak (30% on Y/N, 90% otherwise)",
                  {ExerciseBuilder.TRACESATMC: 0.9,
                   ExerciseBuilder.TRACESATYN: 0.3,
                   ExerciseBuilder.ENGLISHTOLTL: 0.9}),
    ]

    print(f"# Old vs new selection policy — simulated students")
    print(f"(seed {RNG_SEED}, {EXERCISES} exercises x {QUESTIONS_PER_EXERCISE} questions each)\n")

    for arch in archetypes:
        weak = weakest_type(arch)
        print(f"## {arch.name}")
        for policy in ('old', 'new'):
            rng = random.Random(RNG_SEED)
            traj, served, acc = simulate(arch, policy, rng)
            total = sum(served.values())
            weak_share = served[weak] / total
            last10_acc = sum(acc[-10:]) / 10
            print(f"  {policy:>3}: complexity [{fmt_traj(traj)}]"
                  f" | weakest-type share {weak_share:.0%}"
                  f" | accuracy over final 10 exercises {last10_acc:.0%}")
        print()

    print("How to read this:")
    print("- Old-policy complexity is flat at 5 for every archetype by construction;")
    print("  the persistence bug made adaptation impossible. New-policy complexity")
    print("  climbs for strong/improving students and falls to the floor for")
    print("  struggling ones.")
    print("- Old-policy weakest-type share is ~33% (uniform). The new policy")
    print("  concentrates practice on the weak type while the exploration floor")
    print("  keeps every type in rotation.")


if __name__ == '__main__':
    main()
