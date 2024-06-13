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
    if '|' in x:
        print(f"Removing ORs from {word} ---- Modified to {x}")
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


    def __mermaid_str__(self):
        asStr = self.__str__()
        return f'{self.id}["{asStr}"]'
    
    def __str__(self):
        asStr = self.vars
        if '{' in asStr or '}' in asStr:
            print("Warning: Found curly braces in vars")
            print(asStr)
            asStr = asStr.replace('{', '').replace('}', '')
        # Now remove all the parens
        asStr = asStr.replace('(', '').replace(')', '')
        return asStr

    def __add_missing_literals__(self, missing_literals):
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

def mermaidFromSpotTrace(sr):   
    nodeRepr = spotTraceToNodeReprs(sr)
    prefix_states = nodeRepr["prefix_states"]
    cycle_states = nodeRepr["cycle_states"]
    states = prefix_states + cycle_states

    edges = []
    for i in range(1, len(states)):
        current = states[i - 1]
        next = states[i]
        edges.append((current, next))

    return edges

def mermaidGraphFromEdgesList(edges):
    diagramText = 'flowchart LR;'

    for edge in edges:
        diagramText += f'{edge[0].__mermaid_str__()}-->{edge[1].__mermaid_str__()};'

    return diagramText


def genMermaidGraphFromSpotTrace(sr):
    edges = mermaidFromSpotTrace(sr)
    return mermaidGraphFromEdgesList(edges)


def expand_single_trace(sr, literals):
    sr = expandSpotTrace(sr, literals)
    return genMermaidGraphFromSpotTrace(sr)


def change_traces_to_mermaid(data, literals):

    def remove_parens(s):
        return s.replace('(', '').replace(')', '')

    for k in data:
        if k['type'] == ExerciseBuilder.TRACESATMC:
            for option in k['options']:
                sr = option['option']
                sr = expandSpotTrace(sr, literals)                
                option['mermaid'] = genMermaidGraphFromSpotTrace(sr)

                option['option'] = remove_parens(sr)

        elif k['type'] == ExerciseBuilder.TRACESATYN:
            sr = k['trace']
            sr = expandSpotTrace(sr, literals)

            k['trace'] = remove_parens(sr)

            if ("|" in sr):
                print(f"Found OR in trace {sr}")


            k['mermaid'] = genMermaidGraphFromSpotTrace(sr)
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