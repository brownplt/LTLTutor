"""Grammar regression tests for the prose (multi-sentence) translator.

The prose translator may only append verbs ("holds", "occurs", ...) to
literal operands; anything else must be embedded as a full clause. These
tests exercise nested formulas that previously produced double-verb
artifacts like "'e' must hold at all times holds exactly when ...".

Run with:
    python -m pytest test/test_prose_translation.py -v -s
"""

import unittest
import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from unittest.mock import MagicMock
sys.modules['spot'] = MagicMock()

from ltlnode import parse_ltl_string
import ltltoeng_prose as prose


# Nested formulas of the kind SPOT's randltl actually generates for exercises.
NESTED_FORMULAS = [
    "((G e) <-> (X p))",
    "(F (! (G s)))",
    "(X (t <-> (G n)))",
    "((G a) <-> (X b))",
    "(G (X p))",
    "(X (G p))",
    "(F (X p))",
    "(! (G (X p)))",
    "(! (F (G p)))",
    "((X p) U (G q))",
    "((G p) U q)",
    "(p U (X q))",
    "(G ((X p) -> q))",
    "(G (p -> (X (q U s))))",
    "(F ((X p) & q))",
    "(F (p & (X q)))",
    "((! p) -> (G q))",
    "(p -> (X q))",
    "((G p) -> q)",
    "(G ((F p) | (F q)))",
    "(X (X (G p)))",
    "(F (G (X p)))",
    "(G (F (X p)))",
    "(! ((G p) & (F q)))",
    "(! ((X p) | q))",
    "(! (p -> (G q)))",
    "((X p) <-> (X q))",
]

SIMPLE_FORMULAS = [
    "(G p)", "(F p)", "(G (! p))", "(G (p -> (F q)))", "(p U q)",
    "(p -> q)", "(p <-> q)", "(p & q)", "(p | q)", "(! p)", "p",
]

# Word pairs that indicate a verb was appended to a clause that already
# had one.
DOUBLE_VERB_PATTERNS = [
    r"holds holds",
    r"holds\s+exactly when .*at all times holds",
    r"at all times holds",
    r"at all times will cease",
    r"at all times occurs",
    r"at all times must",
    r"occurs occurs",
    r"holds occurs",
    r"occurs holds",
    r"forever holds",
    r"infinitely often holds",
    r"eventually occur holds",
    r"eventually follow holds",
    r"remains true forever (holds|occurs)",
    r", '\w+'\.$",          # sentence ending in a bare, verbless literal
    r"^'\w+'\.$",           # entire sentence is a bare literal
]


class TestProseGrammar(unittest.TestCase):

    def _check(self, formula_str):
        result = prose.translate(parse_ltl_string(formula_str))
        for pat in DOUBLE_VERB_PATTERNS:
            self.assertNotRegex(
                result, pat,
                msg=f"{formula_str} => \"{result}\" matches broken pattern /{pat}/")
        # Every sentence must contain at least one verb-ish token.
        for sentence in re.split(r"(?<=\.)\s+", result):
            self.assertRegex(
                sentence.lower(),
                r"\b(hold|holds|occur|occurs|happen|happens|is|are|becomes?|"
                r"remains?|follow|follows|case|true|excludes|ceases?|cease)\b",
                msg=f"{formula_str} => sentence without a verb: \"{sentence}\" (full: \"{result}\")")
        return result

    def test_nested_formulas_are_grammatical(self):
        print()
        for f in NESTED_FORMULAS:
            result = self._check(f)
            print(f"  {f:28s} => {result}")

    def test_simple_formulas_are_grammatical(self):
        for f in SIMPLE_FORMULAS:
            self._check(f)

    def test_common_patterns_keep_canonical_phrasing(self):
        """The everyday tutoring patterns must keep their concise templates."""
        cases = {
            "(G (p -> (F q)))": "Whenever 'p' holds, 'q' must eventually follow.",
            "(G (! p))":        "'p' never holds.",
            "(G (F p))":        "'p' must occur infinitely often.",
            "(F (G p))":        "Eventually, 'p' becomes true and remains true forever.",
            "(G (p -> (X p)))": "Once 'p' becomes true, it remains true forever.",
        }
        for formula_str, expected in cases.items():
            result = prose.translate(parse_ltl_string(formula_str))
            self.assertEqual(result, expected)

    def test_top_level_literal_gets_verb(self):
        self.assertEqual(prose.translate(parse_ltl_string("p")), "'p' holds.")

    def test_top_level_conjunction_gets_verb(self):
        result = prose.translate(parse_ltl_string("(p & q)"))
        self.assertEqual(result, "Both 'p' and 'q' hold.")


if __name__ == "__main__":
    unittest.main()
