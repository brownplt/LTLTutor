# AGENTS.md — LTL Tutor

Guidelines for AI agents (and human contributors) working in this repository.

---

## Project Overview

LTL Tutor is an adaptive, misconception-driven tutoring system for **Linear Temporal Logic (LTL)**. It is a Flask web application that models common learner misconceptions, adapts exercise selection to individual performance, and provides targeted feedback.

It is used **in live classrooms** — instructors assign exercises during lectures and students complete them in real time on laptops and phones. Reliability, mobile compatibility, and graceful degradation are not nice-to-haves; they are non-negotiable. A bug that skips questions or crashes in front of 40 students during class cannot be reverted fast enough.

---

## Architecture at a Glance

```
┌──────────────────────────────────────────────────────┐
│  Browser (jQuery / Bootstrap 4 / Mermaid.js)         │
│  exercise.html ↔ checkanswers.js + common-func.js    │
└───────────────────────┬──────────────────────────────┘
                        │  HTTP (JSON + form POSTs)
┌───────────────────────▼──────────────────────────────┐
│  Flask (app.py, authroutes.py, modelroutes.py)       │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Exercise   │  │ Feedback     │  │ Auth / RBAC  │ │
│  │ Builder    │  │ Generator    │  │ (Flask-Login) │ │
│  └─────┬──────┘  └──────┬───────┘  └──────────────┘ │
│        │                │                            │
│  ┌─────▼──────┐  ┌──────▼───────┐                    │
│  │ Exercise   │  │ Codebook     │                    │
│  │ Processor  │  │ (misconcep.) │                    │
│  └─────┬──────┘  └──────────────┘                    │
│        │                                             │
│  ┌─────▼──────────────────────────────────────────┐  │
│  │ ltlnode.py (ANTLR parser → AST)                │  │
│  │ spotutils.py (SPOT model checker, traces)      │  │
│  │ ltltoeng.py (LTL → English translation)        │  │
│  │ stepper.py (trace step-through)                │  │
│  │ syntacticmutator.py (formula mutation)         │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  logger.py → SQLAlchemy (SQLite local / Postgres prod)│
└──────────────────────────────────────────────────────┘
```

---

## Repository Layout

```
src/                      Main application source
  app.py                  Flask app entry, all major routes (~1100 lines)
  authroutes.py           Authentication, course/instructor CRUD, user model (ORM)
  modelroutes.py          Model-related API endpoints
  exercisebuilder.py      Adaptive exercise selection (BKT-inspired weighting)
  exerciseprocessor.py    Exercise loading, validation, trace-to-mermaid conversion
  feedbackgenerator.py    Misconception-aware semantic feedback via SPOT
  codebook.py             Misconception enum + mutation rules per misconception
  ltlnode.py              LTL AST node classes, ANTLR parser entry point
  ltltoeng.py             LTL formula → English sentence translation
  spotutils.py            Wrapper around the SPOT library (model checking, traces)
  stepper.py              Per-step trace satisfaction logic
  syntacticmutator.py     Random syntactic formula mutation for distractor generation
  logger.py               SQLAlchemy DB setup, student response logging
  static/                 CSS, JS, prebuilt exercise JSON files
  templates/              Jinja2 HTML templates (exercise UI, auth, instructor tools)

e2e/                      Playwright end-to-end tests
test/                     Unit tests (unittest framework)
experiments/              Research scripts, benchmarks, and notebooks
db/                       Database files (gitignored in production)
```

---

## Development Environment

### Recommended: Docker (zero native dependencies)

```bash
docker compose up          # app on http://localhost:5000
docker compose run e2e     # run Playwright E2E tests against the app
```

Source files are volume-mounted, so edits are reflected on container restart.

### Alternative: Native (requires conda for SPOT)

```bash
conda env create -p .conda -f conda-requirements.txt
conda activate ./.conda
pip install -r requirements.txt
cd src && python app.py
```

### Running Tests

```bash
# Unit tests (from repo root, inside conda env or Docker)
./runtests.sh              # all
./runtests.sh mutation     # mutation tests only
./runtests.sh parsing      # parsing tests only

# E2E tests (requires running app instance)
./run_e2e.sh               # Playwright against localhost:5000
docker compose run e2e     # Playwright via Docker
```

### Dependencies

- **Python packages**: `requirements.txt`. Add pure-Python packages here.
- **Conda packages**: `conda-requirements.txt`. Only for things that cannot be pip-installed (currently just SPOT).
- **E2E test deps**: `e2e/requirements.txt` (pytest-playwright).

---

## How Things Work — What You Need to Know

### User Types & Authentication

Three polymorphic user types via SQLAlchemy single-table inheritance (`authroutes.py`):

| Type | Auth | Created via |
|------|------|-------------|
| `AnonymousStudent` | None (auto-created) | "Quick Start" button |
| `CourseStudent` | Username + course code | Login form |
| `CourseInstructor` | Username + password (hashed) | Signup form |

Flask-Login manages sessions. The `@login_required` decorator gates most routes. Instructor-only routes use `@login_required_as_courseinstructor`.

### Exercise Flow (the critical path)

1. **Load**: JSON exercises come from three sources:
   - `preload:*.json` — static files in `src/static/`
   - `instructor:<id>` — DB-stored exercises created by instructors
   - URL — fetched at request time
2. **Process** (`exerciseprocessor.py`): Options are randomized, traces are converted to Mermaid diagrams, formulas are translated to the student's chosen syntax.
3. **Render** (`exercise.html`): All questions are rendered into the DOM as hidden `.question` cards. One is shown at a time. Navigation is entirely client-side jQuery.
4. **Answer** (`checkanswers.js`): Student selects a radio → "Check Answer" enabled → feedback rendered → "Next Question" enabled.
5. **Log** (`/getfeedback/<type>` route): Each answer is POSTed. Server generates semantic feedback (for English-to-LTL) and logs misconceptions.
6. **Complete**: After the last question, `#done` is shown with a score summary.

**Why this matters**: The entire question progression happens client-side. If JS has a bug (e.g., missing debounce), students can skip questions with no server-side safeguard. Always test the exercise flow end-to-end.

### LTL Parsing

- Entry point: `ltlnode.parse_ltl_string(formula_str)` → returns an `LTLNode` tree.
- Uses ANTLR4 under the hood. **Never call the ANTLR lexer/parser directly** from app code.
- The AST supports multiple syntax renderings (classic, pluscal, JS). Conversion happens via `LTLNode.__str__()` with a syntax parameter.

### SPOT Integration

- All SPOT calls go through `spotutils.py`. **Never `import spot` in other modules.**
- SPOT is a C++ library with Python bindings; it's only available in the conda env or Docker image.
- Key operations: formula equivalence checking, counterexample generation, trace generation, Manna-Pnueli classification.
- SPOT operations can fail on malformed formulas or time out on complex ones. Wrap in try/except.

### Misconception Codebook

- Defined in `codebook.py` as a `MisconceptionCode` enum.
- Each misconception has mutation rules that generate plausible-but-wrong answer options.
- If you add a misconception: update `codebook.py`, add mutation logic, add a feedback template in `templates/misconceptionexplainers/`, and update `feedbackgenerator.py`.

### Adaptive Exercise Builder

- `exercisebuilder.py` uses a BKT-inspired model to estimate per-misconception weights from student response history.
- Weights drive which misconceptions to target in the next generated exercise.
- The model blends recency, frequency, trend, and spaced-repetition signals.

---

## Code Conventions

- **Python**: PEP 8. Python 3.9+ (production runs 3.9 in Docker).
- **Templates**: Jinja2. Keep logic minimal — business logic belongs in Python.
- **JavaScript**: jQuery (not modern ES modules). No build step.
- **Naming**: Python uses `snake_case` for functions/variables. Some legacy code uses `camelCase` (e.g., `userId`) — follow the convention of the file you're editing.

### Key Rules

1. **LTL parsing**: Use `ltlnode.parse_ltl_string()`. Not ANTLR directly.
2. **SPOT calls**: Go through `spotutils.py`. Not `import spot`.
3. **Database queries**: Functions in `authroutes.py` return **detached SQLAlchemy objects** (see Engineering Debt). Extract scalar values you need before the session closes, or be aware that lazy-loaded attributes will fail. See `ENGINEERING-DEBT.md` for details.
4. **Exercise JSON**: Validate with `exerciseprocessor.py`. Don't hand-parse.
5. **Client-side navigation**: The Next button has debounce protection. If you change the exercise template's navigation logic, run the rapid-click E2E tests (`test_exercise_flow.py::TestRapidClickRegression`).

---

## Testing Strategy

### Unit Tests (`test/`)

All use Python `unittest`. Tests must pass before merging.

| File | What it covers |
|------|----------------|
| `test_parsing.py` | LTL formula parsing |
| `test_mutation.py` | Misconception-based formula mutation |
| `test_english_translation.py` | LTL → English pattern matching |
| `test_trace_canonicalization.py` | SPOT trace normalization |
| `test_weighted_trace.py` | Trace weighting logic |
| `test_regression_model.py` | BKT model weight calculation |

### E2E Tests (`e2e/`)

Playwright-based. Run against a live app instance. These are the **regression safety net** for the exercise UI.

| Test class | What it covers |
|------------|----------------|
| `TestExerciseProgression` | Questions display sequentially, one at a time |
| `TestRapidClickRegression` | Rapid/double-tap on Next does NOT skip questions |
| `TestNextButtonDisabledUntilAnswer` | Buttons are properly gated |

### What's NOT Tested (see `ENGINEERING-DEBT.md`)

- Database layer, auth flows, SPOT integration, error paths, concurrent requests, accessibility.

---

## Pull Request Requirements

### Versioning — REQUIRED for every PR

**Every pull request must increment the version number in `src/templates/version.html`.**

Follow [Semantic Versioning](https://semver.org/):

| Change type | Bump |
|---|---|
| Bug fix, minor tweak | Patch (`1.10.0` → `1.10.1`) |
| New feature, backwards-compatible | Minor (`1.10.0` → `1.11.0`) |
| Breaking change or major redesign | Major (`1.10.0` → `2.0.0`) |

### Changelog

Add a brief entry to `CHANGELOG.md` under the current year-month heading (e.g., `## 2026-03`).

### Checklist

- [ ] `./runtests.sh` passes with no errors
- [ ] E2E tests pass (especially if touching exercise flow or templates)
- [ ] `src/templates/version.html` version number incremented
- [ ] `CHANGELOG.md` updated
- [ ] New public functions include docstrings
- [ ] No secrets, credentials, or personal data committed
- [ ] Mobile tested if touching UI (at minimum: run `TestRapidClickRegression`)

---

## Deployment

- Containerized via `Dockerfile`, deployed to Heroku via `heroku.yml`.
- CI: GitHub Actions runs unit tests on PR ([unittest.yaml](.github/workflows/unittest.yaml)) and E2E tests ([e2e.yaml](.github/workflows/e2e.yaml)).
- Release: Tag with `python push_version_tag.py`, which triggers the Docker build + Heroku deploy pipeline.
- Production Python version: specified in `runtime.txt`.
- HTTPS enforced automatically in production.

---

## Self-Hosting

```bash
git clone https://github.com/brownplt/LTLTutor && cd LTLTutor
docker build -t ltltutor:latest .
docker run --rm -it -p 5000:5000 -e SECRET_KEY=$(openssl rand -hex 32) ltltutor
```

Available at `http://localhost:5000`. Supply a strong `SECRET_KEY` for any non-trivial deployment.

---

## Key External Dependencies

| Dependency | Purpose | Notes |
|---|---|---|
| Flask | Web framework | |
| SPOT | LTL model checking and trace generation | C++ with Python bindings; conda-only |
| Flask-Login | User session management | |
| ANTLR4 | LTL grammar parsing (`ltl.g4`) | Runtime only; grammar is pre-compiled |
| SQLAlchemy | ORM / database access | SQLite locally, Postgres in prod |
| Mermaid.js | Trace diagram rendering (client-side) | |
| jQuery 3.5 | DOM manipulation (client-side) | |

---

## Common Pitfalls

1. **"Tests pass locally but fail in CI"** — You're probably not running inside the conda env or Docker. SPOT is not pip-installable. Use `docker compose up` + `docker compose run e2e`.
2. **"Exercise shows blank page"** — Usually a SPOT failure on an invalid formula. Check server logs. The formula may parse but not be valid for SPOT's model checker.
3. **"Students skip to last question"** — This was a real bug (March 2026). The Next button lacked debounce. If you modify exercise navigation, **run the rapid-click E2E tests**.
4. **"DetachedInstanceError from SQLAlchemy"** — Database query functions return objects outside their session scope. See `ENGINEERING-DEBT.md §1`.
5. **"Misconception not appearing in feedback"** — Make sure `codebook.py`, `feedbackgenerator.py`, and the explainer template in `templates/misconceptionexplainers/` are all consistent.

