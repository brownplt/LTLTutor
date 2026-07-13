import datetime
import json
import os
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.modules['spot'] = MagicMock()

from codebook import MisconceptionCode
from logger import Logger, MisconceptionAttempt, MisconceptionOpportunity, StudentResponse


def option(*codes):
    return {
        'value': '+'.join(codes) or 'correct',
        'misconceptions': repr(list(codes)),
    }


class TestOpportunityExtraction(unittest.TestCase):
    def setUp(self):
        self.logger = Logger.__new__(Logger)
        self.attempt = SimpleNamespace(
            id='attempt-1',
            user_id='student',
            timestamp=datetime.datetime(2026, 7, 12, 12, 0, 0),
            correct_answer=False,
            selected_option='',
        )
        self.g = str(MisconceptionCode.ImplicitG)
        self.f = str(MisconceptionCode.ImplicitF)
        self.syntax = str(MisconceptionCode.Syntactic)

    def events(self, options, selected_codes):
        selected_set = set(selected_codes)
        selected = next(
            (
                candidate for candidate in options
                if set(self.logger._parse_misconceptions(candidate['misconceptions'])) == selected_set
            ),
            None,
        )
        self.attempt.selected_option = selected['value'] if selected else ''
        return {
            event.misconception: event
            for event in self.logger._build_opportunity_events(
                self.attempt, options, selected_codes
            )
        }

    def test_selected_coded_distractor_is_positive(self):
        events = self.events([option(self.g), option()], [self.g])
        self.assertEqual(events[self.g].observation, 'positive')
        self.assertEqual(events[self.g].evidence_strength, 1.0)

    def test_correct_answer_is_negative_only_for_displayed_codes(self):
        self.attempt.correct_answer = True
        events = self.events([option(self.g), option()], [])
        self.assertEqual(set(events), {self.g})
        self.assertEqual(events[self.g].observation, 'negative')
        self.assertEqual(events[self.g].evidence_strength, 0.5)

    def test_other_wrong_selection_is_ambiguous_not_mastery(self):
        events = self.events([option(self.g), option(self.f), option()], [self.f])
        self.assertEqual(events[self.f].observation, 'positive')
        self.assertEqual(events[self.g].observation, 'ambiguous')
        self.assertEqual(events[self.g].evidence_strength, 0.0)

    def test_merged_option_splits_positive_evidence(self):
        events = self.events([option(self.g, self.f), option()], [self.g, self.f])
        self.assertEqual(events[self.g].probe_type, 'merged')
        self.assertEqual(events[self.g].evidence_strength, 0.5)
        self.assertEqual(events[self.f].evidence_strength, 0.5)

    def test_selected_merged_option_wins_over_also_displayed_direct_probe(self):
        events = self.events(
            [option(self.g), option(self.g, self.f), option()],
            [self.g, self.f],
        )
        self.assertEqual(events[self.g].probe_type, 'merged')
        self.assertEqual(events[self.g].evidence_strength, 0.5)

    def test_syntactic_control_is_not_a_modeled_opportunity(self):
        events = self.events([option(self.syntax), option()], [self.syntax])
        self.assertEqual(events, {})


class TestOpportunityPersistence(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = os.path.join(self.tempdir.name, 'events.db')
        self.env = patch.dict(os.environ, {'DATABASE_URL': f'sqlite:///{db_path}'})
        self.env.start()
        self.logger = Logger()

    def tearDown(self):
        self.logger.Session.remove()
        self.logger.engine.dispose()
        self.env.stop()
        self.tempdir.cleanup()

    def test_attempt_and_opportunities_are_atomic_and_idempotent(self):
        code = str(MisconceptionCode.ImplicitG)
        options = json.dumps([option(code), option()])
        kwargs = dict(
            userId='student',
            misconceptions=[],
            question_text='G a',
            question_options=options,
            correct_answer=True,
            questiontype='trace_satisfaction_yn',
            mp_class='',
            exercise='exercise',
            course='course',
            selected_option='Yes',
            correct_option='Yes',
            attempt_id='browser-attempt-1',
        )
        self.logger.logStudentResponse(**kwargs)
        self.logger.logStudentResponse(**kwargs)

        with self.logger.Session() as session:
            self.assertEqual(session.query(MisconceptionAttempt).count(), 1)
            self.assertEqual(session.query(MisconceptionOpportunity).count(), 1)
            self.assertEqual(session.query(StudentResponse).count(), 1)
            opportunity = session.query(MisconceptionOpportunity).one()
            self.assertEqual(opportunity.observation, 'negative')

    def test_malformed_option_metadata_degrades_to_an_auditable_attempt(self):
        self.logger.logStudentResponse(
            userId='student',
            misconceptions=[],
            question_text='malformed',
            question_options='not-json',
            correct_answer=True,
            questiontype='english_to_ltl',
            mp_class='',
            exercise='exercise',
            course='course',
            attempt_id='malformed-attempt',
        )
        with self.logger.Session() as session:
            attempt = session.query(MisconceptionAttempt).filter_by(
                question_type='english_to_ltl'
            ).one()
            self.assertEqual(attempt.option_count, 0)
            self.assertEqual(session.query(MisconceptionOpportunity).count(), 0)

    def test_concurrent_duplicate_integrity_error_is_idempotent(self):
        logger = Logger.__new__(Logger)
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        session.get.side_effect = [None, object()]
        session.commit.side_effect = IntegrityError(
            'INSERT misconception_attempts', {}, Exception('duplicate')
        )
        logger.Session = MagicMock(return_value=session)

        logger.logStudentResponse(
            userId='student',
            misconceptions=[],
            question_text='G a',
            question_options=json.dumps([option()]),
            correct_answer=True,
            questiontype='trace_satisfaction_yn',
            mp_class='',
            exercise='exercise',
            course='course',
            selected_option='correct',
            correct_option='correct',
            attempt_id='racing-attempt',
        )

        session.rollback.assert_called_once_with()

    def test_unrelated_integrity_error_is_not_hidden(self):
        logger = Logger.__new__(Logger)
        session = MagicMock()
        session.__enter__.return_value = session
        session.__exit__.return_value = False
        session.get.side_effect = [None, None]
        session.commit.side_effect = IntegrityError(
            'INSERT misconception_attempts', {}, Exception('other constraint')
        )
        logger.Session = MagicMock(return_value=session)

        with self.assertRaises(IntegrityError):
            logger.logStudentResponse(
                userId='student',
                misconceptions=[],
                question_text='G a',
                question_options=json.dumps([option()]),
                correct_answer=True,
                questiontype='trace_satisfaction_yn',
                mp_class='',
                exercise='exercise',
                course='course',
                selected_option='correct',
                correct_option='correct',
                attempt_id='broken-attempt',
            )


if __name__ == '__main__':
    unittest.main()
