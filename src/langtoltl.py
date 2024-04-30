from nl2ltl import translate
from nl2ltl.engines.gpt.core import GPTEngine, Models
from nl2ltl.filters.simple_filters import BasicFilter
from nl2ltl.engines.utils import pretty



### TODO: Does this translate the natural language to LTL? or LTLf?


class LTLTranslator:
    def __init__(self):
        ### TODO: This is currently broken. Something is wrong with how it sets up against GPT. Need to do some digging.
        self.engine = GPTEngine()
        self.filter = BasicFilter()
    
    def natural_lang_to_ltl(self, utterance):
        ltl_formulas = translate(utterance, self.engine, self.filter)
        ltl_formulas = [(str(formula), ltl) for formula, ltl in ltl_formulas]
        return ltl_formulas
