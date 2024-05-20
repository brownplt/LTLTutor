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

def expandSpotTrace(sr, literals):

    if literals == []:
        return sr

    sr = sr.strip()
    if sr == "":
        return ""

    def expandState(s):

        ## TODO: This is wrong -- 1 means taqutology, always true no matter what
        ## 0 means always false no matter what (aka unsat).
        ## So the assignment of variables for 1 doesn't matter
        true_conj = f" {NodeRepr.VAR_SEPARATOR} ".join(literals)
        false_conj = f" {NodeRepr.VAR_SEPARATOR} ".join([f'!{literal}' for literal in literals])

        # I want to replace every instance
        s = re.sub(r'\b1\b', true_conj, s)
        s = re.sub(r'\b0\b', false_conj, s)
        
        vars_words = re.findall(r'\b[a-z0-9]+\b', s)
        missing_literals = [literal for literal in literals if literal not in vars_words]

        for literal in missing_literals:
            x = literal if random.random() < 0.5 else f'!{literal}'
            s = f'{s} {NodeRepr.VAR_SEPARATOR} {x}'
        return s
    
    prefix_split = sr.split('cycle', 1)
    prefix_parts = [x for x in prefix_split[0].strip().split(';') if x.strip() != ""]

    prefix_expanded = [ expandState(s) for s in prefix_parts]
    prefix_string = ';'.join(prefix_expanded)

    ## Would be weird to not have a cycle, but we allow for it.
    if len(prefix_split) > 1:
        cycle = prefix_split[1]
        cycled_content = getCycleContent(cycle)
        cycle_parts = [expandState(s) for s in cycled_content.split(';') if s.strip() != ""]
        
    else:
        cycle_parts = []

    cycle_string = "cycle{" +  ';'.join(cycle_parts) + "}"


    if prefix_string == "":
        return cycle_string
    if cycle_string == "":
        return prefix_string

    return prefix_string + ";" + cycle_string

def getCycleContent(string):
    match = re.match(r'.*\{([^}]*)\}', string)
    return match.group(1) if match else ""

def mermaidFromSpotTrace(sr):   
    sr = sr.strip()
    if sr == "":
        return []


    ## Assuming only one cycle.
    prefix_split = sr.split('cycle', 1)
    prefix_parts = [x for x in prefix_split[0].strip().split(';') if x.strip() != ""]
    states = [NodeRepr(part) for part in prefix_parts]

    ## Would be weird to not have a cycle, but we allow for it.
    if len(prefix_split) > 1:
        cycle = prefix_split[1]
        # Cycle candidate has no string 'cycle' in it here.
        cycled_content = getCycleContent(cycle)
        cycle_states = [NodeRepr(part) for part in cycled_content.split(';') if part.strip() != ""]
        cycle_states.append(cycle_states[0])
        states.extend(cycle_states)

    edges = []
    for i in range(1, len(states)):
        current = states[i - 1]
        next = states[i]
        edges.append((current, next))

    return edges

def mermaidGraphFromEdgesList(edges):
    diagramText = 'flowchart LR;'

    for edge in edges:
        diagramText += f'{str(edge[0])}-->{str(edge[1])};'

    return diagramText

def genMermaidGraphFromSpotTrace(sr):
    edges = mermaidFromSpotTrace(sr)
    return mermaidGraphFromEdgesList(edges)



def expand_single_trace(sr, literals):
    sr = expandSpotTrace(sr, literals)
    return genMermaidGraphFromSpotTrace(sr)


def change_traces_to_mermaid(data, literals):

    for k in data:
        if k['type'] == ExerciseBuilder.TRACESATMC:
            for option in k['options']:
                sr = option['option']
                sr = expandSpotTrace(sr, literals)
                option['option'] = sr

                option['mermaid'] = genMermaidGraphFromSpotTrace(sr)
        elif k['type'] == ExerciseBuilder.TRACESATYN:
            sr = k['trace']
            sr = expandSpotTrace(sr, literals)

            k['trace'] = sr
            k['mermaid'] = genMermaidGraphFromSpotTrace(sr)
    return data

