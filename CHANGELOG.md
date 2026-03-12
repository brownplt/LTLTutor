# Changelog (Feb 2025 and later)

This document summarizes notable updates since February 2025, with commit dates from the repository history for context.【728428†L1-L48】

## 2026-03
- **UX:** Reworked Stepper view into explicit `AST` then `Trace` sections per state, with a standard top-down AST layout and connector lines.
- **UX:** Improved current-state visibility in Stepper traces with stronger highlight styling, state index labels (`sN`), and a `CURRENT` badge on the active node.
- **Bugfix:** Improved trace readability in trace-satisfaction multiple-choice questions by making option trace containers full-width and updating the SVG renderer to size/compress against actual container width instead of a fixed threshold.
- **UX:** Added negation-aware variable coloring in trace diagrams (orange for negated literals, blue for non-negated) to make state labels easier to scan.
- **Dependency:** Removed `openai` from core `requirements.txt`; added `experiments/requirements.txt` for benchmark-only dependencies.
- **New:** Completed full Mermaid.js removal across the entire codebase. All exercise trace diagrams, counterexample traces in feedback, and misconception explainer illustrations now use the custom SVG trace renderer (`tracerenderer.js`) with structured JSON data instead of Mermaid DSL strings. Zero external CDN dependencies for diagram rendering.
- **Cleanup:** Removed all dead Mermaid code from `exerciseprocessor.py` (`genMermaidGraphFromSpotTrace`, `mermaidFromSpotTrace`, `mermaidGraphFromEdgesList`, `expand_single_trace`, `NodeRepr.__mermaid_str__`), `stepper.py` (`treeAsMermaid`, `traceAsMermaid`, `__formula_to_mermaid__`, `__trace_to_mermaid__`), and Mermaid CDN script tags from all templates.
- **Bugfix:** Fixed Stepper mode rendering blank for formulas containing `->` or `<->` (implication/equivalence operators conflicted with Mermaid's arrow syntax in diagram labels).
- **New:** Replaced Mermaid.js with a custom SVG trace renderer (`tracerenderer.js`) in the Stepper page. Renders instantly with zero external dependencies, proper cycle back-edge arcs, and responsive sizing.
- **New:** Replaced Mermaid formula decomposition tree with a CSS-based tree view in the Stepper. Shows satisfied (green) vs unsatisfied (red) subformulae hierarchically.
- **Bugfix:** Fixed rapid-click / double-tap regression on the "Next Question" button that caused students (especially on mobile) to skip directly to the last exercise question. Added debounce guard so each tap advances exactly one question.
- **Bugfix:** Server-side `start_question_index` is now clamped to the valid question range, preventing stale or malicious values from jumping past the last question.
- **New:** Added Playwright E2E test infrastructure (`e2e/`) with regression tests for exercise flow, including rapid-click and mobile-viewport scenarios.
- **New:** Added `docker-compose.yml` and `Dockerfile.e2e` for easy local development and E2E test execution with SPOT pre-installed.
- **New:** Added GitHub Actions E2E workflow (`.github/workflows/e2e.yaml`) so Playwright tests run on every PR.
- **Docs:** Rewrote `AGENTS.md` with full architecture overview, exercise flow walkthrough, common pitfalls, and updated PR checklist.
- **Docs:** Added `ENGINEERING-DEBT.md` cataloguing 14 known debt items with severity, root cause, and proposed fixes.
- **Bugfix:** Fixed `canonicalizeSpotTrace` corrupting SPOT traces containing `|` (OR) in state formulas (e.g. `(s & v) | (!s & !v)`). The canonicalizer now resolves OR operators before reordering literals, preventing garbled traces that caused wrong correct-answer labels on trace satisfaction questions.
- Fixed trace literal canonicalization to normalize both `!` and `¬` negation markers before lexicographic sorting, so variable ordering is stable regardless of glyph choice.
- Fixed instructor exercise preview so it renders the current draft question set (including unsaved editor changes) instead of only the previously saved database state.
- Added explicit save confirmation showing how many questions were persisted for instructor exercises, reducing ambiguity when validating multi-question saves.

## 2025-11
- Improved LTL-to-English translations with grammar smoothing and capitalization applied to pattern-based phrases for more natural summaries.【F:src/ltltoeng.py†L90-L125】【F:src/ltltoeng.py†L827-L835】
- Enhanced instructor experience with dedicated entry points for authoring and managing custom exercises alongside course links.【F:src/templates/instructorhome.html†L76-L109】
- Refined misconception modeling using a Bayesian Knowledge Tracing-inspired weighting scheme that blends recency, frequency, trend, and spaced-repetition drilling signals.【F:src/exercisebuilder.py†L103-L206】
- Revamped student profile page with trend cards and log-scale charts that visualize misconception likelihood over time and surface recent changes.【F:src/templates/student/profile.html†L48-L140】

## 2025-07
- Added table and matrix views to the LTL stepper so learners can inspect subformula satisfaction across trace positions, including a binary matrix layout for cycles.【F:src/templates/stepper.html†L150-L323】

## 2025-05
- Expanded profile and analytics tooling, including misconception trend summaries and improved navigation to logs and generated exercises.【F:src/templates/student/profile.html†L30-L87】
- Added instructor-focused exercise management entry points to streamline course operations.【F:src/templates/instructorhome.html†L60-L94】

## 2025-04
- Introduced Docker-based builds and test automation infrastructure to support deployment and CI workflows.【728428†L35-L48】
