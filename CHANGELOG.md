# Changelog (Feb 2025 and later)

This document summarizes notable updates since February 2025, with commit dates from the repository history for context.【728428†L1-L48】

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
