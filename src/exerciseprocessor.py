import random
import os
import requests
import json
import re
from exercisebuilder import ExerciseBuilder
import ltlnode

def load_questions_from_sourceuri(sourceuri, staticfolderpath):
    if sourceuri.startswith('preload:'):
        sourceuri = sourceuri.replace('preload:', '')
        path_to_json = os.path.join(staticfolderpath, sourceuri)
        with open(path_to_json, 'r') as file:
            return json.load(file)
    elif sourceuri.startswith('instructor:'):
        # Load from instructor-created exercise in database
        exercise_id = sourceuri.replace('instructor:', '')
        from authroutes import get_instructor_exercise_by_id
        exercise = get_instructor_exercise_by_id(int(exercise_id))
        if exercise is None:
            raise Exception(f"Exercise {exercise_id} not found")
        return json.loads(exercise.exercise_json)
    else:
        response = requests.get(sourceuri)
        if response.status_code != 200:
            raise Exception("Error loading exercise")
        return response.json()


## TODO: Maybe we want to change this to ensure some degree of interleaving.
def randomize_questions(data):
    # Randomize question order
    random.shuffle(data)
    # Randomize option order
    for k in data:
        xs = k['options']
        random.shuffle(xs)
        k['options'] = xs
    return data


## Narrow formula
def choosePathFromWord(word):
    asNode = ltlnode.parse_ltl_string(word)
    modifiedNode = removeORs(asNode)
    x = str(modifiedNode)
    return x

# Now go down the word, if there is an OR choose one of left or right at random
def removeORs(node):

    if isinstance(node, ltlnode.OrNode):
        # Choose one of node.left or node.right
        if random.choice([True, False]):
            return removeORs(node.left)
        else:
            return removeORs(node.right)
    elif isinstance(node, ltlnode.BinaryOperatorNode):
        node.left = removeORs(node.left)
        node.right = removeORs(node.right)
    elif isinstance(node, ltlnode.UnaryOperatorNode):
        node.operand = removeORs(node.operand)
    
    return node



class NodeRepr:

    VAR_SEPARATOR = '&'

    def __init__(self, vars):
        self.vars = vars.strip()

        if (not self.vars.startswith('cycle')):
            try:
                vs = choosePathFromWord(self.vars)
                self.vars = vs
            except Exception as e:
                print(f"Error parsing: {self.vars}")
                print(e)

        self.vars = self.vars.replace('&', self.VAR_SEPARATOR)
        self.id = ''.join(random.choices('abcfghijklmopqrstuvwxyzABCFGHIJKLMOPQRSTUVWXYZ', k=6))

    @staticmethod
    def _canonicalize_state(state_str: str) -> str:
        """Return a stable, alphabetically ordered representation of literals in a state."""
        cleaned = state_str.replace('{', '').replace('}', '').strip()
        if cleaned in ("", "unsat"):
            return cleaned

        tokens = [t.strip() for t in re.split(rf'\s*{re.escape(NodeRepr.VAR_SEPARATOR)}\s*', cleaned) if t.strip() != ""]
        normalized = []
        for token in tokens:
            cleaned_token = token.replace('(', '').replace(')', '').strip()
            # Normalize negation markers so sorting is independent of display symbol.
            if cleaned_token.startswith('!') or cleaned_token.startswith('¬'):
                cleaned_token = '!' + cleaned_token[1:].strip()
            normalized.append(cleaned_token)

        def sort_key(token: str):
            is_negated = token.startswith('!')
            name = token[1:] if is_negated else token
            # Sort by name, then place positive before negative for the same name
            return (name, 1 if is_negated else 0)

        ordered = sorted(normalized, key=sort_key)

        # Drop duplicates while preserving the new sorted order
        seen = set()
        deduped = []
        for tok in ordered:
            if tok not in seen:
                seen.add(tok)
                deduped.append(tok)

        return f" {NodeRepr.VAR_SEPARATOR} ".join(deduped)


    def __str__(self):
        asStr = self.vars
        if '{' in asStr or '}' in asStr:
            asStr = asStr.replace('{', '').replace('}', '')
        # Now remove all the parens and order literals alphabetically for stability
        asStr = self._canonicalize_state(asStr)
        return asStr

    def __add_missing_literals__(self, missing_literals):
        missing_literals = sorted(missing_literals)
        s = self.vars
        for literal in missing_literals:
            x = literal if random.random() < 0.5 else f'!{literal}'
            if s == "":
                s = x
            else:
                s = f'({s}) {NodeRepr.VAR_SEPARATOR} {x}'
        self.vars = s


    def expand(self, literals):

        TAUTOLOGY = r'\b1\b'
        UNSAT = r'\b0\b'

        if self.vars == "0":
            self.vars = "unsat"
            return
        
        if self.vars == "1":
            self.vars = ""
        
        s = self.vars
        vars_words = re.findall(r'\b[a-z0-9]+\b', s)
        missing_literals = [literal for literal in literals if literal not in vars_words]
        self.__add_missing_literals__(missing_literals)

## Internal ##
def spotTraceToNodeReprs(sr):
    sr = sr.strip()
    if sr == "":
        return []

    prefix_split = sr.split('cycle', 1)
    prefix_parts = [x for x in prefix_split[0].strip().split(';') if x.strip() != ""]
    states = [NodeRepr(part) for part in prefix_parts]

    cycle_states = []
    ## Would be weird to not have a cycle, but we allow for it.
    if len(prefix_split) > 1:
        cycle = prefix_split[1]
        # Cycle candidate has no string 'cycle' in it here.
        cycled_content = getCycleContent(cycle)
        cycle_states = [NodeRepr(part) for part in cycled_content.split(';') if part.strip() != ""]
        cycle_states.append(cycle_states[0])


    return {
        "prefix_states": states,
        "cycle_states": cycle_states
    }

def nodeReprListsToSpotTrace(prefix_states, cycle_states) -> str:
    prefix_string = ';'.join([str(state) for state in prefix_states])
    cycle_string = "cycle{" +  ';'.join([str(state) for state in cycle_states]) + "}"

    if prefix_string == "":
        return cycle_string
    if cycle_string == "":
        return prefix_string

    return prefix_string + ";" + cycle_string


def _resolve_ors_in_state(state_str: str) -> str:
    """Resolve any OR (|) operators in a SPOT state formula by choosing one branch.
    SPOT traces may contain states like '(s & v) | (!s & !v)' which represent
    multiple valid assignments. This picks one concrete assignment."""
    state_str = state_str.strip()
    if not state_str or state_str in ('1', '0'):
        return state_str
    if '|' not in state_str:
        return state_str
    try:
        return choosePathFromWord(state_str)
    except Exception:
        return state_str


def canonicalizeSpotTrace(sr: str) -> str:
    """
    Return a trace string with each state's literals in canonical order.
    This preserves the original prefix/cycle structure and only normalizes
    literal ordering within states. OR operators in SPOT state formulas are
    resolved first by choosing one concrete assignment.
    """
    sr = sr.strip()
    if sr == "":
        return ""

    prefix_split = sr.split('cycle', 1)
    prefix_parts = [x for x in prefix_split[0].strip().split(';') if x.strip() != ""]
    canonical_prefix = [NodeRepr._canonicalize_state(_resolve_ors_in_state(part)) for part in prefix_parts]

    cycle_parts = []
    if len(prefix_split) > 1:
        cycled_content = getCycleContent(prefix_split[1])
        cycle_parts = [x for x in cycled_content.split(';') if x.strip() != ""]
        cycle_parts = [NodeRepr._canonicalize_state(_resolve_ors_in_state(part)) for part in cycle_parts]

    prefix_string = ';'.join(canonical_prefix)
    if len(cycle_parts) > 0:
        cycle_string = "cycle{" + ';'.join(cycle_parts) + "}"
        if prefix_string == "":
            return cycle_string
        return prefix_string + ";" + cycle_string

    return prefix_string



def expandSpotTrace(sr, literals) -> str:

    nodeRepr = spotTraceToNodeReprs(sr)
    prefix_states = nodeRepr["prefix_states"]
    cycle_states = nodeRepr["cycle_states"]

    if len(literals) > 0:

        for state in prefix_states:
            state.expand(literals)
        for state in cycle_states:
            state.expand(literals)    
    
    sr = nodeReprListsToSpotTrace(prefix_states, cycle_states)
    return sr

def getCycleContent(string):
    match = re.match(r'.*\{([^}]*)\}', string)
    return match.group(1) if match else ""

def _nodeReprDisplayLabel(node_repr):
    """Format a NodeRepr state for display: em-space separator, ¬ negation."""
    asStr = str(node_repr)
    asStr = asStr.replace(NodeRepr.VAR_SEPARATOR, '\u2003')
    asStr = asStr.replace('! ', '!')
    asStr = asStr.replace('!', '\u00ac')
    return asStr


def traceToRenderData(sr):
    """Convert a SPOT trace string into structured data for the SVG trace renderer.
    Returns {prefix: [{label: str}], cycle: [{label: str}]}."""
    node_repr = spotTraceToNodeReprs(sr)
    if not node_repr:
        return {"prefix": [], "cycle": []}

    prefix_states = node_repr["prefix_states"]
    cycle_states = node_repr["cycle_states"]
    # spotTraceToNodeReprs appends cycle_states[0] at the end for the back-edge;
    # drop the duplicate for the render-data representation (the renderer draws
    # the back-edge arc itself).
    if cycle_states and len(cycle_states) > 1:
        cycle_states = cycle_states[:-1]

    return {
        "prefix": [{"label": _nodeReprDisplayLabel(s)} for s in prefix_states],
        "cycle":  [{"label": _nodeReprDisplayLabel(s)} for s in cycle_states]
    }


def change_traces_to_render_data(data, literals):
    """Process exercise data: expand traces and attach structured trace_data for SVG rendering."""

    def remove_parens(s):
        return s.replace('(', '').replace(')', '')

    for k in data:
        if k['type'] == ExerciseBuilder.TRACESATMC:
            for option in k['options']:
                sr = option['option']
                sr = expandSpotTrace(sr, literals)
                option['trace_data'] = traceToRenderData(sr)

                option['option'] = remove_parens(sr)

        elif k['type'] == ExerciseBuilder.TRACESATYN:
            sr = k['trace']
            sr = expandSpotTrace(sr, literals)

            k['trace'] = remove_parens(sr)
            k['trace_data'] = traceToRenderData(sr)
    return data



def getFormulaLiterals(ltlFormula):
    n = ltlnode.parse_ltl_string(ltlFormula)

    literals = set()

    def getLiterals(n):
        if type(n) is ltlnode.LiteralNode:
            literals.add(n.value)
        elif type(n) is ltlnode.UnaryOperatorNode:
            getLiterals(n.operand)
        elif type(n) is ltlnode.BinaryOperatorNode:
            getLiterals(n.left)
            getLiterals(n.right)
    
    getLiterals(n)
    return literals
