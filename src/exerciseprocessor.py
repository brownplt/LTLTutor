import random
import os
import requests
import json
import spotutils
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
    def __init__(self, vars):
        self.vars = vars.strip()

        ## TODO: Or logic

        self.id = ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))

    def __str__(self):
        return f'{self.id}["{self.vars}"]'


def mermaidFromSpotTrace(sr, literals):   
    sr = sr.strip()

    def getCycleContent(string):
        match = re.match(r'.*\{([^}]*)\}', string)
        return match.group(1) if match else ""

    def ensure_literals(node):
        if literals == []:
            return node
        
        vars = node.vars.strip()

        if vars == "1":
            xs = ' & '.join(literals)
            node.vars = xs
            return node

        if vars == "0":
            xs = ' & '.join([f'!{literal}' for literal in literals])
            node.vars = xs
            return node

        vars_words = re.findall(r'\b[a-z0-9]+\b', vars)
        missing_literals = [literal for literal in literals if literal not in vars_words]

        for literal in missing_literals:
            x = literal if random.random() < 0.5 else f'!{literal}'
            vars = f'{vars} & {x}'

        node.vars = vars
        return node

    if sr == "":
        return []

    parts = sr.split(';')
    edges = []
    states = [NodeRepr(part) for part in parts]
    cycleCandidate = states[-1]

    if cycleCandidate.vars.startswith('cycle'):
        cycled_content = getCycleContent(cycleCandidate.vars)
        cycle_states = [NodeRepr(part) for part in cycled_content.split(';')]
        cycle_states.append(cycle_states[0])
        states.pop()
        states.extend(cycle_states)

    try:
        states = [ensure_literals(state) for state in states]
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

