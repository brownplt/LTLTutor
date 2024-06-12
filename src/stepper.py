
from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode
from spotutils import is_trace_satisfied
import re


class StepperNode:
    def __init__(self, children, satisfied, trace):
        self.children = children
        self.satisfied = satisfied
        self.trace = trace
        ## TODO: This SHOULD ALSO HAVE THE TRACE AS MERMAID, WITH THE CURRENT STATE HIGHLIGHTED


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



def satisfiesTrace(node, trace):

    if trace == None or len(trace) == 0:
        return StepperNode([], True, trace)

    if node.isInstanceOf(LiteralNode):
        return StepperNode([], is_trace_satisfied(node, trace), trace)
    elif node.isInstanceOf(UnaryOperatorNode):
        return StepperNode([satisfiesTrace(node.operand, trace)], is_trace_satisfied(node, trace), trace)
    elif node.isInstanceOf(BinaryOperatorNode):
        return StepperNode([satisfiesTrace(node.left, trace), satisfiesTrace(node.right, trace)], is_trace_satisfied(node, trace), trace)
    
    return StepperNode([], False, trace)





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
