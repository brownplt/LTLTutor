# Misconception inference and practice selection

## Decision

LTL Tutor uses a versioned, option-aware **evidence score**, not Bayesian
Knowledge Tracing (BKT), for misconception inference. The score is bounded from
0 to 1 for display, but it is not a calibrated probability.

BKT would be appropriate only after the application has enough explicit
opportunity data to estimate or validate misconception- and question-specific
analogues of slip, guess, repair, and recurrence. Choosing those parameters now
would make an unsupported probability claim. A binary correct/incorrect BKT
observation would also discard the most diagnostic signal already available:
which misconception-coded option the learner selected.

## State and observations

The latent quantity is the current balance of evidence that a cataloged
conceptual misconception is active. `0.5` is the uncertain prior, values below
it mean evidence leans toward absent/resolved, and values above it mean evidence
leans toward present. `RandomSyntactic` remains an experimental control and is
not modeled as a conceptual misconception.

Every submitted answer creates one attempt and one opportunity row for every
cataloged misconception displayed by the question:

| Learner action | Observation | Strength |
|---|---|---|
| Selects a single-code misconception distractor | Positive | 1 |
| Selects a merged misconception distractor | Positive for each carried code | Divided by number of codes |
| Selects the correct answer | Negative for each displayed misconception | Guess-adjusted by option count and divided for merged options |
| Selects a different wrong answer | Ambiguous for unselected misconceptions | 0 |

A negative observation is therefore created only when that misconception was
actually exposed. Overall correctness never updates unrelated misconceptions.
For focused trace yes/no questions, the one coded incorrect verdict is the
explicit probe and a correct verdict supplies negative evidence for its code.

The v1 score sequentially adds documented positive or negative log-evidence,
caps the result away from certainty, and decays stale log-evidence toward the
uncertain prior with a 30-day half-life. Decay means “we are less certain now,”
not “the misconception definitely returned.” These constants are policy values,
not fitted psychometric parameters.

The deliberately simple baseline—increment for a coded wrong answer and
decrement for every correct answer—was rejected because it manufactures
evidence about misconceptions a question did not expose, treats merged options
as identifiable diagnoses, and ignores guessing. V1 keeps the baseline's
transparent directional behavior but makes the unit of evidence an explicit,
auditable opportunity. A single-code selection multiplies evidence odds by 3;
a correct rejection multiplies them by 0.4 after option-count and merge
adjustments. The asymmetry encodes that deliberately choosing a diagnostic
distractor is stronger than merely avoiding it. Synthetic sequence and
property tests cover the consequences; the constants are intentionally not
called fitted parameters.

## Scheduling

Inference and scheduling are separate functions. Candidate and distractor
selection use a monotonic `exploration_floor + evidence_score` weight. This
keeps resolved misconceptions in occasional rotation, gives uncertain ones
normal information-gathering opportunities, and targets high-score
misconceptions more often. Operator-pool scaling is deterministic,
non-compounding, monotonic, and never enables an operator whose base priority is
zero. Multiple-choice questions select at most three conceptual distractors
even when more would fit under the global option cap, so their evidence scores
still affect exposure in smaller candidate sets. Final selection prefers candidates carrying explicit applicable
misconception codes; operator scaling is only a way to improve the candidate
pool.

## Historical data and versions

`student_responses` remains unchanged for existing reports. New structured
events use policy version `option-evidence-v1`. Legacy rows are not silently
converted into negative or positive observations because older records lack a
stable attempt identifier and some question types cannot be reconstructed
without ambiguity. They remain available for an explicit offline replay tool or
future reviewed migration. Until then, a learner with only legacy rows starts
the new misconception model at the documented uncertain prior.

Future fitted BKT or option-tracing models should consume the same attempt and
opportunity tables under a new policy version, be compared by held-out log loss
or Brier score, and retain v1 replay behavior for reproducibility.
