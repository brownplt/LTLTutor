"""Markup hygiene for misconception explainers.

Inline LTL in the explainers is authored in Classic syntax and rewritten in
the browser to the learner's selected syntax (see common-functionality.js).
That mechanism only sees <code class="ltlformula"> elements, so any temporal
operator token in a bare <code> (or in prose) would stay Classic no matter
what the learner picked. These tests keep future explainer edits honest.
"""

import os
import re
import unittest
from html.parser import HTMLParser


EXPLAINER_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../src/templates/misconceptionexplainers",
    )
)

TEMPORAL_TOKEN = re.compile(r"\b[XFGU]\b")


class _ExplainerParser(HTMLParser):
    """Split an explainer into code elements and the surrounding prose."""

    def __init__(self):
        super().__init__()
        self.code_elements = []
        self.prose = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        if tag == "code":
            self._current = {"attrs": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self._current is not None:
            self._current["text"] += data
        else:
            self.prose.append(data)

    def handle_endtag(self, tag):
        if tag == "code" and self._current is not None:
            self.code_elements.append(self._current)
            self._current = None


def _parse_explainers():
    for filename in sorted(os.listdir(EXPLAINER_DIR)):
        if not filename.endswith(".html"):
            continue
        with open(os.path.join(EXPLAINER_DIR, filename)) as f:
            parser = _ExplainerParser()
            parser.feed(f.read())
        yield filename, parser


class TestMisconceptionExplainerMarkup(unittest.TestCase):
    def test_explainers_exist(self):
        self.assertTrue(list(_parse_explainers()))

    def test_temporal_code_fragments_are_syntax_aware(self):
        for filename, parser in _parse_explainers():
            with self.subTest(explainer=filename):
                self.assertTrue(parser.code_elements)
                for element in parser.code_elements:
                    classes = set(element["attrs"].get("class", "").split())
                    if TEMPORAL_TOKEN.search(element["text"]):
                        self.assertIn(
                            "ltlformula",
                            classes,
                            f"<code>{element['text']}</code> contains a "
                            "temporal operator but lacks the ltlformula "
                            "class, so it would not follow the selected "
                            "syntax",
                        )

    def test_no_temporal_tokens_in_prose(self):
        for filename, parser in _parse_explainers():
            with self.subTest(explainer=filename):
                prose = " ".join(parser.prose)
                self.assertIsNone(
                    TEMPORAL_TOKEN.search(prose),
                    "temporal operator tokens must be wrapped in "
                    '<code class="ltlformula"> to follow the selected syntax',
                )


if __name__ == "__main__":
    unittest.main()
