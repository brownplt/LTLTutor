from nl2ltl import translate
from nl2ltl.engines.gpt.core import GPTEngine, Models
from nl2ltl.filters.simple_filters import BasicFilter
from nl2ltl.engines.utils import pretty

engine = GPTEngine()
filter = BasicFilter()
utterance = "Eventually send me a Slack after receiving a Gmail"

ltlf_formulas = translate(utterance, engine, filter)
pretty(ltlf_formulas)

### TODO: THis becomes a service (Present them all, with confidence?)