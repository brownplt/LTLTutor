"""Regression tests for the exercise flow.

These tests verify that:
- Every question is shown one at a time in order.
- Rapid clicking on "Next Question" does NOT skip questions.
- The completion screen only appears after the last question.
"""

import re
import pytest
from playwright.sync_api import expect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_prebuilt_exercise(page, base_url, exercise_file="robotrain.json"):
    """Navigate to the predefined exercise page for a prebuilt JSON file."""
    page.goto(f"{base_url}/exercise/predefined?sourceuri=preload:{exercise_file}")
    page.wait_for_selector("#questions")


def _visible_question_cards(page):
    """Return a list of currently visible .question cards."""
    return page.locator(".question").filter(has_text=re.compile(".")).all()


def _count_visible_questions(page):
    """Count how many .question cards are currently visible (display != none)."""
    return page.locator(".question:visible").count()


def _current_question_number(page):
    """Parse 'Question X of Y' from the visible question card."""
    visible = page.locator(".question:visible")
    text = visible.locator("small.text-muted").inner_text()
    m = re.search(r"Question (\d+) of (\d+)", text)
    assert m, f"Could not parse question number from: {text}"
    return int(m.group(1)), int(m.group(2))


def _answer_and_advance(page):
    """Select the first radio option, check the answer, then click Next."""
    visible = page.locator(".question:visible")
    # Remember the current question number so we can detect advance
    text = visible.locator("small.text-muted").inner_text()
    m = re.search(r"Question (\d+) of (\d+)", text)
    current_q = int(m.group(1))
    total_q = int(m.group(2))

    # Pick the first radio
    visible.locator("input[type=radio]").first.check()
    # Click "Check Answer"
    visible.locator("button.checkanswer").click()
    # Wait for next button to become enabled (feedback POST may be in-flight)
    page.wait_for_function(
        "document.querySelector('.question:not([style*=\"display: none\"]) button.next')?.disabled === false",
        timeout=10000,
    )
    # Click "Next Question"
    page.locator(".question:visible button.next").click()
    # Wait for the visible question to actually change (or #done to appear)
    if current_q < total_q:
        page.wait_for_function(
            f"""(() => {{
                const vis = document.querySelector('.question:not([style*="display: none"])');
                if (!vis) return false;
                const t = vis.querySelector('small.text-muted')?.textContent || '';
                const m = t.match(/Question (\\d+) of/);
                return m && parseInt(m[1]) > {current_q};
            }})()""",
            timeout=5000,
        )
    else:
        page.wait_for_function(
            "document.getElementById('done')?.style.display !== 'none'",
            timeout=5000,
        )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExerciseProgression:
    """Verify that exercises progress one question at a time."""

    def test_first_question_visible_on_load(self, logged_in_page, base_url):
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        assert _count_visible_questions(page) == 1
        q_num, total = _current_question_number(page)
        assert q_num == 1
        assert total >= 1

    def test_sequential_progression(self, logged_in_page, base_url):
        """Walking through each question shows them in strict order."""
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        _, total = _current_question_number(page)

        for expected in range(1, total + 1):
            assert _count_visible_questions(page) == 1, f"More than one question visible at step {expected}"
            q_num, _ = _current_question_number(page)
            assert q_num == expected, f"Expected question {expected}, got {q_num}"

            if expected < total:
                _answer_and_advance(page)
            else:
                # Last question — answer and advance should show #done
                _answer_and_advance(page)
                expect(page.locator("#done")).to_be_visible()

    def test_done_not_visible_before_last_question(self, logged_in_page, base_url):
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        _, total = _current_question_number(page)
        if total <= 1:
            pytest.skip("Exercise has only one question")

        # Answer question 1 and advance
        _answer_and_advance(page)
        expect(page.locator("#done")).not_to_be_visible()


class TestRapidClickRegression:
    """Regression: rapid clicking must NOT skip questions (the reported bug)."""

    def test_rapid_next_clicks_do_not_skip(self, logged_in_page, base_url):
        """Simulate rapid double/triple-clicks on 'Next Question'.

        This is the exact scenario that caused the classroom regression
        where mobile users were skipped to the last question.
        """
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        _, total = _current_question_number(page)
        if total <= 2:
            pytest.skip("Need at least 3 questions to test rapid clicking")

        # Answer question 1 so Next is enabled
        visible = page.locator(".question:visible")
        visible.locator("input[type=radio]").first.check()
        visible.locator("button.checkanswer").click()
        page.wait_for_function(
            "document.querySelector('.question:not([style*=\"display: none\"]) button.next')?.disabled === false"
        )

        # Rapidly click the Next button multiple times with no delay
        next_btn = visible.locator("button.next")
        next_btn.click()
        next_btn.click(force=True)
        next_btn.click(force=True)

        # After rapid clicks, we should be on question 2 — NOT question 4+
        page.wait_for_timeout(500)  # Let debounce settle
        assert _count_visible_questions(page) == 1, "Multiple questions visible after rapid clicks"

        q_num, _ = _current_question_number(page)
        assert q_num == 2, f"Rapid clicks skipped to question {q_num} — expected question 2"

        # And #done should definitely NOT be visible
        expect(page.locator("#done")).not_to_be_visible()

    def test_rapid_clicks_on_mobile_viewport(self, logged_in_page, base_url):
        """Same rapid-click test but with a mobile viewport size."""
        page = logged_in_page
        page.set_viewport_size({"width": 375, "height": 812})  # iPhone X

        _load_prebuilt_exercise(page, base_url)

        _, total = _current_question_number(page)
        if total <= 2:
            pytest.skip("Need at least 3 questions to test rapid clicking")

        # Answer and enable Next
        visible = page.locator(".question:visible")
        visible.locator("input[type=radio]").first.check()
        visible.locator("button.checkanswer").click()
        page.wait_for_function(
            "document.querySelector('.question:not([style*=\"display: none\"]) button.next')?.disabled === false"
        )

        # Rapid clicks
        next_btn = visible.locator("button.next")
        next_btn.click()
        next_btn.click(force=True)
        next_btn.click(force=True)

        page.wait_for_timeout(500)
        assert _count_visible_questions(page) == 1

        q_num, _ = _current_question_number(page)
        assert q_num == 2, f"Mobile rapid clicks skipped to question {q_num}"
        expect(page.locator("#done")).not_to_be_visible()


class TestNextButtonDisabledUntilAnswer:
    """Verify the Next button is disabled until the user answers."""

    def test_next_disabled_initially(self, logged_in_page, base_url):
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        next_btn = page.locator(".question:visible button.next")
        expect(next_btn).to_be_disabled()

    def test_check_answer_disabled_until_selection(self, logged_in_page, base_url):
        page = logged_in_page
        _load_prebuilt_exercise(page, base_url)

        check_btn = page.locator(".question:visible button.checkanswer")
        expect(check_btn).to_be_disabled()

        # Select a radio
        page.locator(".question:visible input[type=radio]").first.check()
        expect(check_btn).to_be_enabled()
