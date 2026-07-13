"""Option-aware misconception evidence inference and scheduling policy.

The score produced here is deliberately *not* presented as a calibrated
probability.  It is a bounded representation of accumulated likelihood-ratio
style evidence.  The constants are policy choices which can later be replaced
by fitted BKT/IRT parameters without changing the opportunity event contract.
"""

import datetime
import math


MODEL_VERSION = "option-evidence-v1"
PRIOR_SCORE = 0.5
MIN_SCORE = 0.05
MAX_SCORE = 0.95

# A selected, single-code misconception distractor is stronger evidence than a
# correct rejection is counter-evidence.  Neither observation can create
# certainty, and merged options divide their evidence across their codes.
POSITIVE_LOG_LIKELIHOOD = math.log(3.0)
NEGATIVE_LOG_LIKELIHOOD = math.log(0.4)

# In the absence of new opportunities, evidence becomes less decisive and
# drifts toward the uncertain prior.  This is uncertainty decay, not an
# assertion that a misconception has definitely recurred.
EVIDENCE_HALF_LIFE_HOURS = 30 * 24

# Scheduling is separate from inference.  Even a resolved misconception keeps
# an exploration floor, while higher evidence scores are targeted more often.
SCHEDULING_EXPLORATION_FLOOR = 0.25


def modeled_codes(misconception_enum):
    """Return conceptual misconception codes, excluding syntactic controls."""
    return [
        str(code) for code in misconception_enum
        if getattr(code, "name", "") != "Syntactic"
    ]


def _logit(value):
    value = min(MAX_SCORE, max(MIN_SCORE, value))
    return math.log(value / (1.0 - value))


def _sigmoid(value):
    return 1.0 / (1.0 + math.exp(-value))


def _event_value(event, name, default=None):
    if isinstance(event, dict):
        return event.get(name, default)
    return getattr(event, name, default)


def _decay(log_odds, elapsed_hours):
    if elapsed_hours <= 0:
        return log_odds
    retention = 0.5 ** (elapsed_hours / EVIDENCE_HALF_LIFE_HOURS)
    return log_odds * retention


def calculate_evidence_score(events, now=None):
    """Calculate one misconception's uncalibrated evidence score.

    Events must expose ``timestamp``, ``observation`` (``positive``,
    ``negative``, or ``ambiguous``), and ``evidence_strength``.  Ambiguous
    opportunities are retained for audit/replay but do not move the score.
    """
    if now is None:
        now = datetime.datetime.now()

    ordered = sorted(
        events,
        key=lambda event: _event_value(event, "timestamp", datetime.datetime.min),
    )
    log_odds = _logit(PRIOR_SCORE)
    previous_time = _event_value(ordered[0], "timestamp", now) if ordered else now

    for event in ordered:
        timestamp = _event_value(event, "timestamp", previous_time)
        elapsed = max(0.0, (timestamp - previous_time).total_seconds() / 3600.0)
        log_odds = _decay(log_odds, elapsed)

        strength = max(0.0, min(1.0, float(_event_value(event, "evidence_strength", 0.0))))
        observation = _event_value(event, "observation", "ambiguous")
        if observation == "positive":
            log_odds += POSITIVE_LOG_LIKELIHOOD * strength
        elif observation == "negative":
            log_odds += NEGATIVE_LOG_LIKELIHOOD * strength

        log_odds = min(_logit(MAX_SCORE), max(_logit(MIN_SCORE), log_odds))
        previous_time = timestamp

    if ordered:
        elapsed = max(0.0, (now - previous_time).total_seconds() / 3600.0)
        log_odds = _decay(log_odds, elapsed)

    return min(MAX_SCORE, max(MIN_SCORE, _sigmoid(log_odds)))


def scheduling_weight(evidence_score):
    """Map inference to a monotonic practice-selection weight with a floor."""
    score = min(1.0, max(0.0, evidence_score))
    return SCHEDULING_EXPLORATION_FLOOR + score
