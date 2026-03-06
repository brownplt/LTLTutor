# AGENTS.md — LTL Tutor

Guidelines for AI agents (and human contributors) working in this repository.

---

## Project Overview

LTL Tutor is an adaptive, misconception-driven tutoring system for **Linear Temporal Logic (LTL)**. It is a Flask web application that models common learner misconceptions, adapts exercise selection to individual performance, and provides targeted feedback.

---

## Repository Layout

```
src/                  Main application source
  app.py              Flask app entry point and route definitions
  authroutes.py       Authentication and course/instructor routes
  modelroutes.py      Routes for model-related endpoints
  exercisebuilder.py  Adaptive exercise selection logic (BKT-inspired)
  exerciseprocessor.py  Parses and validates exercise definitions
  feedbackgenerator.py  Misconception-aware feedback generation
  codebook.py         Misconception codebook definitions
  ltlnode.py          LTL AST nodes and parser entry point
  ltltoeng.py         LTL-to-English translation
  spotutils.py        SPOT library integration for LTL model checking
  stepper.py          Trace satisfaction step-through logic
  syntacticmutator.py Syntactic formula mutation for exercise generation
  static/             CSS, JS, and JSON data assets
  templates/          Jinja2 HTML templates

test/                 Unit tests (unittest-based)
experiments/          Research scripts, benchmarks, and notebooks
db/                   Database-related files
```

---

## Development Environment

### Setup

```bash
conda env create -p .conda -f conda-requirements.txt
conda activate ./.conda
pip install -r requirements.txt
```

### Running the App

```bash
cd src
python app.py
```

The server defaults to port `5000`. Set the `PORT` environment variable to override.

### Dependencies

- Python packages are in `requirements.txt`.
- Conda-specific dependencies (including SPOT) are in `conda-requirements.txt`.
- Do **not** add pure-Python packages to `conda-requirements.txt`; use `requirements.txt` instead.

---

## Testing

Run the full test suite from the repository root:

```bash
./runtests.sh           # all tests
./runtests.sh mutation  # mutation tests only
./runtests.sh parsing   # parsing tests only
```

Tests live in `test/` and follow the `test_*.py` naming convention. All tests use Python's built-in `unittest` framework.

**Before opening a PR, the full test suite must pass cleanly.**

---

## Pull Request Requirements

### Versioning — REQUIRED for every PR

**Every pull request must increment the version number in [src/templates/version.html](src/templates/version.html).**

The file contains a single semantic version string, e.g.:

```
1.9.8
```

Follow [Semantic Versioning](https://semver.org/):

| Change type | Bump |
|---|---|
| Bug fix, minor tweak | Patch (`1.9.8` → `1.9.9`) |
| New feature, backwards-compatible | Minor (`1.9.8` → `1.10.0`) |
| Breaking change or major redesign | Major (`1.9.8` → `2.0.0`) |

Do not open a PR without updating this file.

### Changelog

Add a brief entry to `CHANGELOG.md` describing what changed and why. Group entries under the current year-month heading (e.g., `## 2026-03`), creating one if it does not exist.

### Checklist

- [ ] `./runtests.sh` passes with no errors
- [ ] `src/templates/version.html` version number incremented
- [ ] `CHANGELOG.md` updated with a summary of changes
- [ ] New public functions and modules include docstrings
- [ ] No secrets, credentials, or personal data committed

---

## Code Conventions

- **Language:** Python 3; follow PEP 8.
- **Templates:** Jinja2; keep logic minimal — business logic belongs in Python.
- **LTL parsing:** Use `ltlnode.parse_ltl_string()` as the primary entry point; do not call the ANTLR lexer/parser directly from application code.
- **Model checking:** Route SPOT calls through `spotutils.py`; do not import `spot` directly in other modules.
- **Misconception codebook:** If adding or modifying misconceptions, update `codebook.py` and ensure consistency with the feedback templates in `feedbackgenerator.py`.
- **Exercises:** Exercise definitions are JSON-based; use `exerciseprocessor.py` for validation and `exercisebuilder.py` for adaptive selection.

---

## Deployment

- The app is containerised via `Dockerfile` and deployed to Heroku via `heroku.yml`.
- The production runtime Python version is specified in `runtime.txt`.
- HTTPS is enforced automatically in production; HTTP is allowed locally.
- To tag and push a release version: `python push_version_tag.py`.

---

## Self-Hosting

The LTL Tutor can be run locally or on your own server as a Docker image.

**1. Clone the repository:**

```bash
git clone https://github.com/brownplt/LTLTutor
cd LTLTutor
```

**2. Build the Docker image:**

```bash
docker build -t ltltutor:latest .
```

**3. Run the container:**

```bash
docker run --rm -it -p 5000:5000 -e SECRET_KEY=secret ltltutor
```

The tutor will be available at `http://localhost:5000`.

> **Note:** LTL Tutor uses session-based authentication, so you must supply a `SECRET_KEY` environment variable. Replace `secret` above with a strong, unique value for any non-trivial deployment.

---

## Key External Dependencies

| Dependency | Purpose |
|---|---|
| Flask | Web framework |
| SPOT | LTL model checking and trace generation |
| Flask-Login | User session management |
| ANTLR4 | LTL grammar parsing (`ltl.g4`) |

