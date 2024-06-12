
from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode
from spotutils import is_trace_satisfied
import re
import random

def randid():
    ''.join(random.choices('abcfghijklmopqrstuvwxyzABCFGHIJKLMOPQRSTUVWXYZ', k=6))


class StepperNode:
    def __init__(self, formula, children, satisfied, trace):
        self.children = children
        self.satisfied = satisfied
        self.trace = trace
        id = randid()

        ## TODO: need the current formula ##
        self.formula = formula



    def __to__mermaid__(self):
        edges = []
        # Set the color based on satisfaction
            # THis should happen based on mermaid class

        ###
        if self.satisfied:
            noderepr = f'{self.id}["{self.formula}"]:::satclass'
        else:
            noderepr = f'{self.id}[["{self.formula}"]]:::unsatclass'
        
        for child in self.children:
            child_repr = f'{child.id}["{child.formula}"]'
            edges += f'{noderepr}-->{child_repr}'


            child_edges = child.__to_mermaid__()
            edges += child_edges
        return edges


    ## TODO: Function to render this as a mermaid tree
    def __to_mermaid_full__(self):
        
        prefix = 'flowchart LR;'

        
        
        # Formula, and choose its color based on satisfaction
        # Formula should have an arrow to each child.
        # Each child should have a color based on satisfaction.

        postfix = 'classDef unsatclass fill:#f96'

        pass



class TraceSatisfactionResult:
    def __init__(self, prefix_states, cycle_states):
        self.prefix_states = prefix_states
        self.cycle_states = cycle_states

    def to_dict(self):
        return {
            "prefix_states": self.prefix_states,
            "cycle_states": self.cycle_states
        }

    def __repr__(self):
        return f"TraceSatisfactionResult(prefix_states={self.prefix_states}, cycle_states={self.cycle_states})"


    def __to_mermaid__(self):
        ## TODO: return a mermaid string, highligting the current node. (maybe state index?)
        pass

def satisfiesTrace(node, trace):

    formula = str(node)
    if trace == None or len(trace) == 0:
        return StepperNode(formula, [], True, trace)

    if node.isInstanceOf(LiteralNode):
        return StepperNode(formula, [], is_trace_satisfied(node, trace), trace)
    elif node.isInstanceOf(UnaryOperatorNode):
        return StepperNode(formula, [satisfiesTrace(node.operand, trace)], is_trace_satisfied(node, trace), trace)
    elif node.isInstanceOf(BinaryOperatorNode):
        return StepperNode(formula, [satisfiesTrace(node.left, trace), satisfiesTrace(node.right, trace)], is_trace_satisfied(node, trace), trace)
    
    return StepperNode(formula, [], False, trace)





def splitTraceAtCycle(sr):

    def getCycleContent(string):
        match = re.match(r'.*\{([^}]*)\}', string)
        return match.group(1) if match else ""
    
    prefix_split = sr.split('cycle', 1)
    prefix_states = [x.strip() for x in prefix_split[0].strip().split(';') if x.strip() != ""]

    cycle_states = []
    ## Would be weird to not have a cycle, but we allow for it.
    if len(prefix_split) > 1:
        cycle = prefix_split[1]
        cycled_content = getCycleContent(cycle)
        cycle_states = [s.strip() for s in cycled_content.split(';') if s.strip() != ""]
        
    else:
        cycle_states = []

    return prefix_states, cycle_states


# Trace has to be a list of spot word formulae
def traceSatisfactionPerStep(node, trace):
    if len[trace] == 0:
        return []
    
    ## TODO: What about cycles ##
    ## We should probably unfold, or 'know' we are in a cycle. So perhaps a 
    ## We SPLIT on the cycle. Do the prefix. THEN do the cycle, where we know we are in a cycle.

    prefix, cycle = splitTraceAtCycle(trace)

    ## Now for each prefix state, we check if the trace is satisfied.
    ## However, we need the cycle to be part of the entire trace

    def buildTraceForStateInPrefix(prefix_index):
        prefix_string = prefix[prefix_index:].join(';')

        if len(cycle) == 0:
            return prefix_string
        else:
            cycle_string = "cycle{" +  ';'.join(cycle) + "}"
            return prefix_string + ";" + cycle_string
        
    def buildTraceForStateInCycle(cycle_index):

        if len(cycle) == 0:
            return []
        
        ## Unroll one cycle, from the current state
        cycle_prefix_string = cycle[cycle_index:].join(';')
        if len(cycle_prefix_string) == 0:
            return []

        
        cycle_string = "cycle{" +  ';'.join(cycle) + "}"
        return cycle_prefix_string + ";" + cycle_string
    
    prefix_sat = [satisfiesTrace(node, buildTraceForStateInPrefix(i)) for i in range(len(prefix))]
    cycle_sat = [satisfiesTrace(node, buildTraceForStateInCycle(i)) for i in range(len(cycle))]
    return TraceSatisfactionResult(prefix_sat, cycle_sat)
