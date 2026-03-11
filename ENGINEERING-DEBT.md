# Engineering Debt — LTL Tutor

This document catalogues known technical debt, architectural issues, and improvement opportunities. It is meant to be honest and actionable — each item describes what's wrong, why it matters, what a fix looks like, and how risky it is to leave as-is.

Last updated: March 2026.

---

## Table of Contents

1. [SQLAlchemy Session Detachment](#1-sqlalchemy-session-detachment)
2. [Client-Trusts-Itself Answer Verification](#2-client-trusts-itself-answer-verification)
3. [Non-Atomic Response Logging](#3-non-atomic-response-logging)
4. [Multiple Logger Instances / Duplicate DB Engines](#4-multiple-logger-instances--duplicate-db-engines)
5. [SPOT Error Handling](#5-spot-error-handling)
6. [No CSRF Protection](#6-no-csrf-protection)
7. [Exercise JSON Validation](#7-exercise-json-validation)
8. [Test Coverage Gaps](#8-test-coverage-gaps)
9. [Ad-Hoc Schema Migrations](#9-ad-hoc-schema-migrations)
10. [Hardcoded Configuration](#10-hardcoded-configuration)
11. [Naming Inconsistencies](#11-naming-inconsistencies)
12. [Accessibility](#12-accessibility)
13. [Incomplete LTL-to-English Coverage](#13-incomplete-ltl-to-english-coverage)
14. [Open TODOs in Code](#14-open-todos-in-code)
15. [LTL Core Should Be an Extractable Package](#15-ltl-core-should-be-an-extractable-package)

---

## 1. SQLAlchemy Session Detachment

**Severity: High** — causes intermittent `DetachedInstanceError` in production.

### The problem

Several functions in `authroutes.py` return full ORM objects from inside a `with Session() as session:` block. Once the block exits, those objects are **detached** — any access to a lazy-loaded attribute raises `DetachedInstanceError`:

```python
# authroutes.py
def get_instructor_exercise_by_id(exercise_id):
    with Session() as session:
        exercise = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        return exercise  # ← detached after this line

# app.py — later, outside the session:
exercise.owner  # works (was eagerly loaded)
exercise.some_relationship  # ← DetachedInstanceError
```

Affected functions:
- `get_exercises_for_course()`
- `get_course_exercise_by_name()`
- `get_instructor_exercise_by_name()`
- `get_instructor_exercise_by_id()`
- `load_user()` (Flask-Login user loader)

### Why it matters

In practice this works *most of the time* because the columns accessed in `app.py` (`exercise_json`, `name`, `allow_multiple_submissions`, `expires_at`) are all eagerly-loaded column attributes, not relationships. But it's a landmine: any new code that accesses a relationship or adds a deferred column will crash at runtime, and only on certain code paths.

### What a fix looks like

**Option A (minimal):** Extract the needed scalars into a dict/namedtuple inside the session:

```python
def get_instructor_exercise_by_id(exercise_id):
    with Session() as session:
        ex = session.query(InstructorExercise).filter_by(id=exercise_id).first()
        if ex is None:
            return None
        return {
            'id': ex.id, 'name': ex.name, 'owner': ex.owner,
            'exercise_json': ex.exercise_json, ...
        }
```

**Option B (better):** Use `expire_on_commit=False` in the sessionmaker so returned objects keep their loaded state. Or use a request-scoped session (Flask-SQLAlchemy pattern) so objects stay attached for the entire request.

---

## 2. Client-Trusts-Itself Answer Verification

**Severity: Medium** — allows score inflation; not a data-loss risk.

### The problem

In `checkanswers.js`, the client determines whether the answer is correct by comparing the selected radio's value to the `data-correct="True"` attribute in the HTML. It then sends `correct: true/false` to the server:

```javascript
let correct = selected_option == correct_option;
let data = {
    selected_option: selected_radio.value,
    correct_option: correct_radio.value,
    correct: correct,  // client-computed
    misconceptions: selected_radio.dataset.misconceptions,
    ...
};
```

The server logs whatever `correct` value it receives without rechecking. Additionally, all correct answers are visible in the page source (the `data-correct="True"` attribute).

### Why it matters

Students can trivially inspect the HTML to find correct answers. Motivated students can POST `correct: true` for every question. This inflates analytics and undermines the adaptive model.

### What a fix looks like

The server already receives both `selected_option` and `correct_option`. It should compute `isCorrect = (selected_option == correct_option)` server-side and ignore the client's `correct` field. The correct answer can stay in the HTML for now (it enables instant client-side feedback), but the server should be the authority for logging.

---

## 3. Non-Atomic Response Logging

**Severity: Medium** — causes partial log entries on interrupted requests.

### The problem

`logger.py`'s `logStudentResponse()` loops over misconceptions and calls `self.record()` for each one. Each `record()` call opens a separate session and commits independently:

```python
def logStudentResponse(self, userId, misconceptions, ...):
    if misconceptions is None or len(misconceptions) == 0:
        log = StudentResponse(...)
        self.record(log)  # separate transaction

    for misconception in misconceptions:
        log = StudentResponse(...)
        self.record(log)  # another separate transaction
```

If a request is interrupted after 2 of 5 misconceptions, the database has a partial record. There's also no idempotency key, so retried requests create duplicate rows.

### What a fix looks like

Batch all inserts into a single session/transaction:

```python
def logStudentResponse(self, ...):
    records = []
    if not misconceptions:
        records.append(StudentResponse(..., misconception=""))
    else:
        for m in misconceptions:
            records.append(StudentResponse(..., misconception=m))

    with self.Session() as session:
        session.add_all(records)
        session.commit()
```

---

## 4. Multiple Logger Instances / Duplicate DB Engines

**Severity: Low** — wastes connections; no functional bug today.

### The problem

`app.py` and `modelroutes.py` each create their own `Logger()` instance. Each `Logger.__init__()` creates a new SQLAlchemy engine and scoped session factory. Meanwhile, `authroutes.py` creates *another* engine at module scope for its own ORM tables.

This means 3 separate connection pools to the same database, with no shared transaction coordination.

### What a fix looks like

Create one engine and one session factory at application startup. Pass them to `Logger`, `authroutes`, and `modelroutes` via dependency injection or a shared module.

---

## 5. SPOT Error Handling

**Severity: High** — causes blank exercises in production.

### The problem

SPOT operations (`spotutils.py`) can fail in several ways:
- Malformed formula strings → `spot.parse_formula()` throws
- Complex formulas → automaton construction hangs or OOMs
- Complement construction → fails on certain formula classes

Most call sites in `exercisebuilder.py` and `app.py` have no try/except around SPOT calls. When SPOT fails, the exception propagates and the student either sees a 500 error or a blank exercise.

### What a fix looks like

Wrap all SPOT calls in `spotutils.py` with try/except. Return `None` or empty results on failure. Log the formula that caused the failure. Callers should check for `None` and degrade gracefully (e.g., skip that exercise, show a message).

---

## 6. No CSRF Protection

**Severity: Medium** — standard web vulnerability; no known exploit in the wild.

### The problem

None of the forms (login, signup, exercise creation, answer submission) include CSRF tokens. An attacker could trick a logged-in instructor into submitting a hidden form that creates/modifies exercises.

### What a fix looks like

Add Flask-WTF or manually include a CSRF token in all POST forms. Flask-WTF makes this straightforward with `{{ form.hidden_tag() }}` or `{{ csrf_token() }}`.

---

## 7. Exercise JSON Validation

**Severity: Medium** — malformed exercises crash at runtime with unhelpful errors.

### The problem

When instructors create exercises, the server validates that the payload is a JSON list, but does not check:
- That each question has required fields (`type`, `question`, `options`)
- That `type` is one of the three known values (`englishtoltl`, `tracesatisfaction_mc`, `tracesatisfaction_yn`)
- That `options` is a non-empty array
- That exactly one option has `isCorrect: true`
- That misconception codes match the `MisconceptionCode` enum

Malformed exercises pass validation and then crash when rendered in the template (Jinja2 `KeyError`) or in JavaScript (undefined property).

### What a fix looks like

Add a `validate_exercise_json(data)` function in `exerciseprocessor.py` that checks structure, field presence, types, and value domains. Call it before saving to the database and before rendering.

---

## 8. Test Coverage Gaps

**Severity: High** — the areas with zero coverage are the ones most likely to cause production incidents.

### What's tested

| Area | Coverage |
|------|----------|
| LTL parsing | Good (happy paths) |
| Formula mutation | Good |
| English translation | Good |
| Trace canonicalization | Good |
| Trace weighting | Good |
| BKT model | Good |

### What's NOT tested

| Area | Risk |
|------|------|
| Database layer (`logger.py`, `authroutes.py` queries) | High — detached-object bugs, transaction issues |
| Authentication / authorization flows | High — permission bypasses |
| SPOT integration (`spotutils.py`) | High — formula failure recovery |
| Exercise generation end-to-end | High — the critical user path |
| Client-side JavaScript | High — the "skip to last question" bug lived here |
| Error paths (malformed formulas, DB errors, SPOT timeouts) | Medium |
| Concurrent requests | Medium |
| Input validation / boundary cases | Medium |

### What would help most

1. **Flask test client tests** for the exercise flow: load → answer → feedback → complete.
2. **Playwright E2E tests** (now added in `e2e/`) — expand to cover auth flows, instructor exercise creation, and syntax switching.
3. **SQLite in-memory database tests** for `logger.py` and `authroutes.py` query functions.
4. **SPOT mock tests** for `exercisebuilder.py` to verify graceful degradation.

---

## 9. Ad-Hoc Schema Migrations

**Severity: Medium** — works today but will cause pain as the schema evolves.

### The problem

`authroutes.py` handles schema evolution with raw ALTER TABLE statements:

```python
def _ensure_instructor_exercise_schema():
    existing_columns = {col['name'] for col in inspector.get_columns(INSTRUCTOR_EXERCISE_TABLE)}
    with engine.begin() as connection:
        if 'expires_at' not in existing_columns:
            connection.execute(text(f"ALTER TABLE {INSTRUCTOR_EXERCISE_TABLE} ADD COLUMN expires_at VARCHAR"))
```

This approach:
- Has no rollback on failure
- Has no version tracking (can't tell what state the schema is in)
- Uses string SQL that isn't portable across database backends
- Runs on every app startup, adding latency

### What a fix looks like

Adopt Alembic for migration management. Each schema change becomes a versioned migration file with `upgrade()` and `downgrade()` functions.

---

## 10. Hardcoded Configuration

**Severity: Low** — works but makes deployment and testing harder.

| Item | Location | Issue |
|------|----------|-------|
| Database path | `logger.py` | Hardcoded to `db/database.db`; no env override for local SQLite path |
| Secret key | `app.py` | `os.environ.get('SECRET_KEY')` — silently becomes `None` if unset, which disables session security |
| Port | `app.py` | `os.getenv('PORT', '5000')` — no validation that it's a valid integer |
| Benchmark CSV paths | `app.py` | Relative to `PROJECT_ROOT`; breaks if working directory changes |

### What a fix looks like

Centralize configuration in a config module. Use `python-dotenv` for local dev. Fail loudly if `SECRET_KEY` is unset in non-debug mode.

---

## 11. Naming Inconsistencies

**Severity: Low** — causes confusion for new contributors but no functional bugs.

| Pattern | Examples |
|---------|----------|
| `userId` vs `user_id` | `app.py` uses `userId`, `logger.py` column is `user_id` |
| `exerciseName` vs `exercise_name` | `logger.py` column is `exerciseName`, parameters use `exercise_name` |
| Question type strings | `"english_to_ltl"` in routes vs `"englishtoltl"` in exercise JSON |

Convention: new code should use `snake_case`. Don't rename existing database columns (would require a migration), but keep Python variable names consistent.

---

## 12. Accessibility

**Severity: Medium** — the app is used in classrooms; some students may need assistive technology.

Known gaps:
- Mermaid diagrams have `aria-label` set to raw trace strings, which aren't meaningful to screen readers.
- Feedback uses color alone (green/red backgrounds) without text indicators — fails for colorblind users.
- No skip-to-content links.
- Screen readers aren't notified when questions change (no ARIA live regions).
- Radio button labels rely on complex nested HTML; association is fragile.

---

## 13. Incomplete LTL-to-English Coverage

**Severity: Low** — produces awkward but not incorrect translations.

The pattern-based translator (`ltltoeng.py`) handles common formula shapes well but falls back to mechanical, hard-to-read translations for:
- Deeply nested temporal operators (e.g., `G(F(G(p)))`)
- Complex Until precedence variations
- Formulas with more than 3 literals

The `choose_best_sentence()` function uses Zipf word frequency to pick the most natural phrasing, but the tuning is empirical and some patterns are missing entirely.

---

## 14. Open TODOs in Code

Collected from grep. These are commitments-in-code that haven't been addressed:

| File | Note |
|------|------|
| `exercisebuilder.py` | "We want complexity to be persistent for user, and scale up or down" — complexity model is placeholder |
| `codebook.py` | "This one is tricky, less meaningful..." — `OtherImplicit` misconception logic is uncertain |
| `stepper.py` | "Over here:" — incomplete comment, unclear what was intended |
| `spotutils.py` | "Examine: Perhaps not so many trues and falses?" — trace generation may emit redundant states |
| `exerciseprocessor.py` | "Maybe we want to change this to ensure some degree of interleaving" — option randomization question |
| `exercise.html` | "TODO: Should this stay?" — Mermaid SVG width hack |
| `exercise.html` | "TODO: Disable this, and then re-enable" — Next button comment (now addressed with debounce) |

---

## 15. LTL Core Should Be an Extractable Package

**Severity: Low** — no runtime impact, but limits reuse and creates tight coupling.

### The problem

The LTL parsing, AST, semantic mutation, and misconception codebook form a self-contained core that has no dependency on Flask, the database, or the web layer. Today these modules (`ltlnode.py`, `syntacticmutator.py`, `codebook.py`, `spotutils.py`, `ltltoeng.py`) are embedded in the `src/` directory alongside the web app, with no public API boundary.

This means:
- Other projects that want to parse and mutate LTL formulas must vendor the entire repo.
- There's no enforced separation between "LTL engine" and "web app" — any module can `import app` or `import logger` and nobody would notice until it becomes a circular dependency.
- Testing the core in isolation requires the full app environment (Flask, SQLAlchemy, etc.) on the import path.

### The dependency graph of the extractable core

```
ltlnode.py          ← ANTLR4 (runtime only)
  ↑
syntacticmutator.py ← copy, random
  ↑
codebook.py         ← ltlnode, spotutils
  ↑
spotutils.py        ← spot (C++ bindings)
ltltoeng.py         ← ltlnode, inflect, wordfreq
```

None of these import Flask, SQLAlchemy, or any web-layer module.

### What a fix looks like

Extract these into a pip-installable package (e.g., `ltlcore` or `pyltl`):

```
ltlcore/
  __init__.py        # exports parse_ltl_string, LTLNode, mutate, etc.
  ltlnode.py
  syntacticmutator.py
  codebook.py
  spotutils.py
  ltltoeng.py
  grammar/           # ANTLR .g4 and generated files
setup.py / pyproject.toml
```

The web app would then `pip install ltlcore` (or use a path dependency during development) and import from it. This enforces the boundary, makes the core independently testable and versioned, and lets researchers and other tools use LTL parsing + semantic mutation without pulling in the tutor.
