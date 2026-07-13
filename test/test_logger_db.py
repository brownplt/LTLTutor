"""DB-layer tests for logger.Logger against a throwaway SQLite database.

Covers the durable side of the answer path: that responses are written with the
right fields, that repeated submissions are deduplicated (idempotency -- the
safeguard against double-tap / retry creating phantom answers), and that the
submission counter used to gate one-submission exercises counts *distinct*
questions. The logger is constructed against a temp DB captured at __init__, so
these tests never touch the real db/database.db and don't depend on env state
after import.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

sys.modules.setdefault("spot", MagicMock())
sys.modules.setdefault("inflect", MagicMock())
sys.modules.setdefault("wordfreq", MagicMock(zipf_frequency=lambda *a, **k: 0))

_TMPDIR = tempfile.mkdtemp(prefix="ltltutor_loggertest_")
_PREV_DB_URL = os.environ.get("DATABASE_URL")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_TMPDIR, 'logger.db')}"

from logger import Logger, StudentResponse, MisconceptionAttempt  # noqa: E402

# Capture a Logger bound to the temp DB, then restore the environment so this
# module doesn't reconfigure sibling tests that read DATABASE_URL later.
LOGGER = Logger()
if _PREV_DB_URL is None:
    os.environ.pop("DATABASE_URL", None)
else:
    os.environ["DATABASE_URL"] = _PREV_DB_URL


def tearDownModule():
    LOGGER.engine.dispose()
    shutil.rmtree(_TMPDIR, ignore_errors=True)


def _log(user, *, misconceptions=None, question_text="Q?", correct=True,
         questiontype="englishtoltl", exercise="ex1", attempt_id=None,
         options=None):
    options = options if options is not None else [{"option": "F a", "isCorrect": True}]
    LOGGER.logStudentResponse(
        userId=user,
        misconceptions=misconceptions,
        question_text=question_text,
        question_options=json.dumps(options),
        correct_answer=correct,
        questiontype=questiontype,
        mp_class="",
        exercise=exercise,
        course="",
        attempt_id=attempt_id,
    )


def _responses_for(user):
    with LOGGER.Session() as session:
        return session.query(StudentResponse).filter(StudentResponse.user_id == user).all()


def _attempts_for(user):
    with LOGGER.Session() as session:
        return session.query(MisconceptionAttempt).filter(MisconceptionAttempt.user_id == user).count()


class TestLogStudentResponse(unittest.TestCase):
    def test_writes_response_with_expected_fields(self):
        _log("u_fields", question_text="Eventually a", correct=True, questiontype="englishtoltl")
        rows = _responses_for("u_fields")
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row.question_text, "Eventually a")
        self.assertTrue(row.correct_answer)
        self.assertEqual(row.question_type, "englishtoltl")
        self.assertEqual(row.misconception, "")  # no misconceptions -> empty marker

    def test_one_legacy_row_per_misconception(self):
        _log("u_multi", misconceptions=["ExclusiveU", "ImplicitG"], correct=False)
        rows = _responses_for("u_multi")
        self.assertEqual(len(rows), 2)
        self.assertEqual({r.misconception for r in rows}, {"ExclusiveU", "ImplicitG"})

    def test_no_misconceptions_writes_single_empty_row(self):
        _log("u_none", misconceptions=[])
        rows = _responses_for("u_none")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].misconception, "")


class TestIdempotency(unittest.TestCase):
    """A stable attempt_id must make re-submission a no-op, so a double-tap or a
    retried request never inflates a student's recorded answers."""

    def test_same_attempt_id_is_deduplicated(self):
        _log("u_idem", misconceptions=["ExclusiveU"], correct=False, attempt_id="attempt-123")
        after_first = len(_responses_for("u_idem"))
        attempts_first = _attempts_for("u_idem")

        # Identical resubmission (same user + attempt_id) must add nothing.
        _log("u_idem", misconceptions=["ExclusiveU"], correct=False, attempt_id="attempt-123")
        self.assertEqual(len(_responses_for("u_idem")), after_first)
        self.assertEqual(_attempts_for("u_idem"), attempts_first)

    def test_distinct_attempt_ids_create_separate_records(self):
        _log("u_distinct", correct=True, attempt_id="attempt-A")
        _log("u_distinct", correct=True, attempt_id="attempt-B")
        self.assertEqual(_attempts_for("u_distinct"), 2)

    def test_same_attempt_id_different_users_are_independent(self):
        _log("u_shareA", correct=True, attempt_id="shared-attempt")
        _log("u_shareB", correct=True, attempt_id="shared-attempt")
        self.assertEqual(_attempts_for("u_shareA"), 1)
        self.assertEqual(_attempts_for("u_shareB"), 1)


class TestTypeValidation(unittest.TestCase):
    def test_non_string_user_id_is_rejected(self):
        with self.assertRaises(ValueError):
            LOGGER.logStudentResponse(
                userId=12345, misconceptions=[], question_text="q",
                question_options="[]", correct_answer=True, questiontype="englishtoltl",
                mp_class="", exercise="ex", course="",
            )

    def test_non_bool_correct_answer_is_rejected(self):
        with self.assertRaises(ValueError):
            LOGGER.logStudentResponse(
                userId="u", misconceptions=[], question_text="q",
                question_options="[]", correct_answer="yes", questiontype="englishtoltl",
                mp_class="", exercise="ex", course="",
            )


class TestSubmissionCounter(unittest.TestCase):
    """getUserExerciseResponses gates one-submission-only exercises."""

    def test_counts_distinct_questions_not_raw_rows(self):
        # Answering the SAME question twice (e.g., a resubmit) must count once,
        # otherwise a student could be locked out after re-answering one item.
        _log("u_count", question_text="Q1", exercise="quiz", attempt_id="c1")
        _log("u_count", question_text="Q1", exercise="quiz", attempt_id="c2")
        self.assertEqual(LOGGER.getUserExerciseResponses("u_count", "quiz"), 1)

        _log("u_count", question_text="Q2", exercise="quiz", attempt_id="c3")
        self.assertEqual(LOGGER.getUserExerciseResponses("u_count", "quiz"), 2)

    def test_counter_is_scoped_by_exercise_and_user(self):
        _log("u_scopeA", question_text="Q1", exercise="exX", attempt_id="s1")
        _log("u_scopeA", question_text="Q1", exercise="exY", attempt_id="s2")
        self.assertEqual(LOGGER.getUserExerciseResponses("u_scopeA", "exX"), 1)
        self.assertEqual(LOGGER.getUserExerciseResponses("u_scopeA", "exY"), 1)
        # A different user has answered nothing for exX.
        self.assertEqual(LOGGER.getUserExerciseResponses("u_scopeB", "exX"), 0)

    def test_getCompletedExercises(self):
        _log("u_done", question_text="Q1", exercise="done_ex", attempt_id="d1")
        _log("u_done", question_text="Q2", exercise="done_ex", attempt_id="d2")
        completed = LOGGER.getCompletedExercises("u_done", [("done_ex", 2), ("other_ex", 1)])
        self.assertIn("done_ex", completed)
        self.assertNotIn("other_ex", completed)


class TestAttemptTranslationMode(unittest.TestCase):
    """The experiment arm must land on the attempt row itself, so
    opportunity-level analyses (arm x misconception) join attempts directly
    instead of reconstructing the arm from legacy per-code response rows."""

    def test_attempt_row_records_translation_mode(self):
        LOGGER.logStudentResponse(
            userId="u_mode",
            misconceptions=[],
            question_text="policy question",
            question_options="[]",
            correct_answer=True,
            questiontype="englishtoltl",
            mp_class="",
            exercise="mode_ex",
            course="",
            translation_mode="contextualizeddeontic",
            attempt_id="mode-1",
        )
        with LOGGER.Session() as session:
            row = session.query(MisconceptionAttempt).filter(
                MisconceptionAttempt.user_id == "u_mode").one()
        self.assertEqual(row.translation_mode, "contextualizeddeontic")

    def test_startup_migration_adds_column_to_existing_table(self):
        """A deployment whose misconception_attempts table predates the
        column must get it added by Logger's startup schema check."""
        import sqlite3
        from logger import Logger, MISCONCEPTION_ATTEMPT_TABLE

        tmpdir = tempfile.mkdtemp(prefix="ltltutor_migr_")
        db_path = os.path.join(tmpdir, "old.db")
        con = sqlite3.connect(db_path)
        con.execute(
            f"CREATE TABLE {MISCONCEPTION_ATTEMPT_TABLE} "
            "(id VARCHAR PRIMARY KEY, user_id VARCHAR)")
        con.commit()
        con.close()

        prev = os.environ.get("DATABASE_URL")
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
        try:
            migrated = Logger()
            migrated.engine.dispose()
            # Inspect via sqlite directly: Logger's Inspector caches the
            # pre-migration reflection it did during the schema check.
            con = sqlite3.connect(db_path)
            columns = {row[1] for row in con.execute(
                f"PRAGMA table_info({MISCONCEPTION_ATTEMPT_TABLE})")}
            con.close()
            self.assertIn("translation_mode", columns)
        finally:
            if prev is None:
                os.environ.pop("DATABASE_URL", None)
            else:
                os.environ["DATABASE_URL"] = prev
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
