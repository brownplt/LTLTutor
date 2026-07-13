"""Flask integration tests for the critical student path: log in, answer a
question, get feedback, and have the response recorded.

This is the endpoint students hit hardest during a live class -- every answer
POSTs to /getfeedback/<questiontype> -- and it was previously at 0% coverage.

Scope & design:
  * A temporary on-disk SQLite database (shared by logger + authroutes) is wired
    up via DATABASE_URL *before* importing app, so the test never touches the
    real db/database.db. The env var is cleared after import so later test files
    aren't affected; the app's engines have already captured the URI.
  * spot is mocked (sibling convention). The SPOT-heavy branch of /getfeedback
    only runs for INCORRECT answers; that exact logic (FeedbackGenerator,
    traceSatisfactionPerStep) is covered directly by test_feedbackgenerator.py
    and test_stepper.py. Here we exercise the HTTP layer: auth gating, routing,
    request handling, and durable logging -- none of which need real SPOT.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# --- wire a throwaway DB + secret before importing app -----------------------
_TMPDIR = tempfile.mkdtemp(prefix="ltltutor_flowtest_")
_DB_PATH = os.path.join(_TMPDIR, "flowtest.db")
_PREV_DB_URL = os.environ.get("DATABASE_URL")
_PREV_SECRET = os.environ.get("SECRET_KEY")
os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH}"
os.environ["SECRET_KEY"] = "integration-test-secret"

sys.modules.setdefault("spot", MagicMock())
sys.modules.setdefault("inflect", MagicMock())
sys.modules.setdefault("wordfreq", MagicMock(zipf_frequency=lambda *a, **k: 0))

# Flask is a production dependency (present in Docker/CI and any real dev env),
# but skip gracefully rather than error in a minimal environment that lacks it.
try:
    import app as appmod  # noqa: E402
    from logger import StudentResponse  # noqa: E402  (bound to the temp DB)
    APP_AVAILABLE = True
except Exception:  # pragma: no cover - only hit when flask/app deps are absent
    APP_AVAILABLE = False

# Restore the environment so importing app here doesn't reconfigure sibling
# tests that read DATABASE_URL later. The engines created during import above
# have already captured the temp URI.
if _PREV_DB_URL is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _PREV_DB_URL


def tearDownModule():
    shutil.rmtree(_TMPDIR, ignore_errors=True)


def _count_responses():
    with appmod.answer_logger.Session() as session:
        return session.query(StudentResponse).count()


class _BaseFlowTest(unittest.TestCase):
    def setUp(self):
        if not APP_AVAILABLE:
            self.skipTest("flask app not importable in this environment")
        appmod.app.config["TESTING"] = True
        self.client = appmod.app.test_client()

    def _login_anonymous(self):
        resp = self.client.post(
            "/login", data={"user_type": "anonymous-student"}, follow_redirects=False
        )
        # Successful login redirects to the index.
        self.assertEqual(resp.status_code, 302)
        return resp

    @staticmethod
    def _feedback_payload(**overrides):
        payload = {
            "selected_option": "F a",
            "correct_option": "F a",
            "correct": True,
            "misconceptions": "[]",
            "question_text": "Eventually a holds.",
            "question_options": [{"option": "F a", "isCorrect": True}],
        }
        payload.update(overrides)
        return payload


class TestAuthGating(_BaseFlowTest):
    def test_index_requires_login(self):
        # login_required routes redirect anonymous browsers to the login page.
        resp = self.client.get("/", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_getfeedback_requires_login(self):
        resp = self.client.post(
            "/getfeedback/english_to_ltl", json=self._feedback_payload()
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_anonymous_login_grants_access(self):
        self._login_anonymous()
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)


class TestGetFeedbackHappyPath(_BaseFlowTest):
    def setUp(self):
        super().setUp()
        self._login_anonymous()

    def test_english_to_ltl_correct_answer_records_response(self):
        before = _count_responses()
        resp = self.client.post(
            "/getfeedback/english_to_ltl", json=self._feedback_payload(correct=True)
        )
        self.assertEqual(resp.status_code, 200)
        # A correct English-to-LTL answer returns no counterexample feedback.
        self.assertEqual(json.loads(resp.get_data(as_text=True)), {})
        self.assertEqual(_count_responses(), before + 1)

    def test_trace_satisfaction_yn_correct_answer_records_response(self):
        before = _count_responses()
        resp = self.client.post(
            "/getfeedback/trace_satisfaction_yn",
            json=self._feedback_payload(selected_option="yes", correct_option="yes"),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_count_responses(), before + 1)

    def test_trace_satisfaction_mc_correct_answer_records_response(self):
        before = _count_responses()
        resp = self.client.post(
            "/getfeedback/trace_satisfaction_mc", json=self._feedback_payload()
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_count_responses(), before + 1)

    def test_unknown_question_type_is_handled_not_crashed(self):
        resp = self.client.post(
            "/getfeedback/some_unknown_type", json=self._feedback_payload()
        )
        # The route returns a controlled message rather than a 500.
        self.assertEqual(resp.status_code, 200)
        self.assertIn("INVALID QUESTION TYPE", resp.get_data(as_text=True))


class TestMisconceptionLogging(_BaseFlowTest):
    def setUp(self):
        super().setUp()
        self._login_anonymous()

    def test_each_reported_misconception_is_logged_as_a_row(self):
        # logStudentResponse writes one StudentResponse per reported misconception
        # (see ENGINEERING-DEBT.md sec.3). Two misconceptions -> two rows.
        before = _count_responses()
        payload = self._feedback_payload(
            correct=False,
            misconceptions="['ExclusiveU', 'ImplicitG']",
        )
        resp = self.client.post("/getfeedback/trace_satisfaction_mc", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_count_responses(), before + 2)

    def test_no_misconceptions_still_logs_one_row(self):
        before = _count_responses()
        payload = self._feedback_payload(correct=True, misconceptions="[]")
        resp = self.client.post("/getfeedback/trace_satisfaction_mc", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(_count_responses(), before + 1)


class TestExerciseLoadDegradation(_BaseFlowTest):
    def setUp(self):
        super().setUp()
        self._login_anonymous()

    def test_unknown_exercise_reports_not_found_without_crashing(self):
        resp = self.client.get("/exercise/load/no-such-exercise-xyz")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("not found", resp.get_data(as_text=True).lower())


class TestMalformedPayloadContract(_BaseFlowTest):
    """Characterization: /getfeedback assumes a well-formed JSON payload. A
    missing required field currently surfaces as a server error rather than a
    validated 400. Documented here so any future hardening is a deliberate
    change (a defensive 400 would be a reasonable improvement)."""

    def setUp(self):
        super().setUp()
        self._login_anonymous()
        # Let the view's exception propagate to the test instead of being
        # swallowed into a generic 500, so we can assert on it precisely.
        appmod.app.config["TESTING"] = True

    def test_missing_required_field_is_not_silently_accepted(self):
        before = _count_responses()
        with self.assertRaises(KeyError):
            self.client.post("/getfeedback/english_to_ltl", json={"correct": True})
        # Nothing was logged for the malformed request.
        self.assertEqual(_count_responses(), before)


if __name__ == "__main__":
    unittest.main()
