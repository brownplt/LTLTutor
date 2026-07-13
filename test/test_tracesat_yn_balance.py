import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
sys.modules['spot'] = MagicMock()

from codebook import MisconceptionCode
from exercisebuilder import ExerciseBuilder


class TraceYesNoBuilder(ExerciseBuilder):
    def __init__(self):
        super().__init__([])
        self.code = str(MisconceptionCode.ImplicitG)

    def get_options_with_misconceptions_as_formula(self, answer):
        return [
            {'option': 'a', 'isCorrect': False, 'misconceptions': [self.code]},
            {'option': answer, 'isCorrect': True, 'misconceptions': []},
        ]

    def _full_misconception_weights(self):
        return {self.code: 0.9}


class TestTraceYesNoAnswerBalance(unittest.TestCase):
    @patch('exerciseprocessor.canonicalizeSpotTrace', side_effect=lambda trace: trace)
    @patch('exercisebuilder.spotutils.weighted_trace_choice', side_effect=lambda traces: traces[0])
    @patch('exercisebuilder.spotutils.generate_traces')
    @patch('exercisebuilder.spotutils.generate_accepted_traces', return_value=['a; cycle{a}'])
    @patch('exercisebuilder.random.random', return_value=0.1)
    @patch('exercisebuilder.random.choices', side_effect=lambda candidates, **kwargs: [candidates[0]])
    def test_positive_instance_makes_yes_correct_without_diagnostic_code(
        self, _choices, _random, _accepted, rejected, _weighted, _canonicalize
    ):
        question = TraceYesNoBuilder().build_tracesat_yn_question('G a')
        yes, no = question['options']
        self.assertTrue(yes['isCorrect'])
        self.assertFalse(no['isCorrect'])
        self.assertEqual(yes['misconceptions'], [])
        self.assertEqual(no['misconceptions'], [])
        rejected.assert_not_called()

    @patch('exerciseprocessor.canonicalizeSpotTrace', side_effect=lambda trace: trace)
    @patch('exercisebuilder.spotutils.weighted_trace_choice', side_effect=lambda traces: traces[0])
    @patch('exercisebuilder.spotutils.generate_traces', return_value=['a; cycle{a}'])
    @patch('exercisebuilder.spotutils.generate_accepted_traces')
    @patch('exercisebuilder.random.random', return_value=0.9)
    @patch('exercisebuilder.random.choices', side_effect=lambda candidates, **kwargs: [candidates[0]])
    def test_diagnostic_negative_instance_makes_no_correct_and_codes_yes(
        self, _choices, _random, accepted, rejected, _weighted, _canonicalize
    ):
        builder = TraceYesNoBuilder()
        question = builder.build_tracesat_yn_question('G a')
        yes, no = question['options']
        self.assertFalse(yes['isCorrect'])
        self.assertTrue(no['isCorrect'])
        self.assertEqual(yes['misconceptions'], [builder.code])
        self.assertEqual(no['misconceptions'], [])
        accepted.assert_not_called()
        rejected.assert_called_once()


if __name__ == '__main__':
    unittest.main()
