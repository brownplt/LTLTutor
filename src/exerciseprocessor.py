import random
import os
import requests
import json
import re
from exercisebuilder import ExerciseBuilder

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


class NodeRepr:

    VAR_SEPARATOR = '&'

    def __init__(self, vars):
        self.vars = vars.strip()

        ## TODO: Or logic
        if (not self.vars.startswith('cycle')) and "|" in self.vars:
            vs = self.vars.split('|')[0]
            self.vars = vs

        self.vars = self.vars.replace('&', self.VAR_SEPARATOR)
        self.id = ''.join(random.choices('abcfghijklmopqrstuvwxyzABCFGHIJKLMOPQRSTUVWXYZ', k=6))

    def __str__(self):
        asStr = self.vars
        if '{' in asStr or '}' in asStr:
            print("Warning: Found curly braces in vars")
            print(asStr)
            asStr = asStr.replace('{', '').replace('}', '')
        asStr = asStr.replace('(', '').replace(')', '')
        return f'{self.id}["{asStr}"]'

def ensure_literals(node, literals):
    if literals == []:
        return node
    
    vars = node.vars.strip()

    if vars == "1":
        xs = f" {NodeRepr.VAR_SEPARATOR} ".join(literals)
        node.vars = xs
        return node

    if vars == "0":
        xs = f" {NodeRepr.VAR_SEPARATOR} ".join([f'!{literal}' for literal in literals])
        node.vars = xs
        return node

    vars_words = re.findall(r'\b[a-z0-9]+\b', vars)
    missing_literals = [literal for literal in literals if literal not in vars_words]

    for literal in missing_literals:
        x = literal if random.random() < 0.5 else f'!{literal}'
        vars = f'{vars} {NodeRepr.VAR_SEPARATOR} {x}'

    node.vars = vars
    return node

def getCycleContent(string):
    match = re.match(r'.*\{([^}]*)\}', string)
    return match.group(1) if match else ""

def mermaidFromSpotTrace(sr, literals):   
    sr = sr.strip()
    if sr == "":
        return []


    ## Assuming only one cycle.
    prefix_split = sr.split('cycle', 1)
    prefix_parts = [x for x in prefix_split[0].strip().split(';') if x.strip() != ""]
    states = [NodeRepr(part) for part in prefix_parts]

    ## Would be weird to not have a cycle, but we allow for it.
    if len(prefix_parts) > 1:
        cycle = prefix_split[1]
        # Cycle candidate has no string 'cycle' in it here.
        cycled_content = getCycleContent(cycle)
        cycle_states = [NodeRepr(part) for part in cycled_content.split(';') if part.strip() != ""]
        cycle_states.append(cycle_states[0])
        states.extend(cycle_states)

    edges = []

    try:
        states = [ensure_literals(state, literals) for state in states]
    except Exception as e:
        print("Ensure literals failed")
        print(e)

    for i in range(1, len(states)):
        current = states[i - 1]
        next = states[i]
        edges.append((current, next))

    return edges

def mermaidGraphFromEdgesList(edges):
    diagramText = 'flowchart LR;\n'

    for edge in edges:
        diagramText += f'{str(edge[0])}-->{str(edge[1])};'

    return diagramText

def genMermaidGraphFromSpotTrace(sr, literals):
    edges = mermaidFromSpotTrace(sr, literals)
    return mermaidGraphFromEdgesList(edges)


def expandSpotTrace(sr, literals):
    sr = sr.strip()
    if sr == "":
        return []





    simple_split = sr.split(';')

    expanded = [ ensure_literals(s, literals) for s in simple_split]
    return expanded.join(';')



def change_traces_to_mermaid(data, literals):

    for k in data:
        if k['type'] == ExerciseBuilder.TRACESATMC:
            for option in k['options']:
                sr = option['option']
                option['mermaid'] = genMermaidGraphFromSpotTrace(sr, literals)
        elif k['type'] == ExerciseBuilder.TRACESATYN:
            sr = k['trace']
            k['mermaid'] = genMermaidGraphFromSpotTrace(sr, literals)
    return data

