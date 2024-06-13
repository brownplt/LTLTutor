
from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode
from spotutils import is_trace_satisfied
import re
import random
from exerciseprocessor import mermaidFromSpotTrace, mermaidGraphFromEdgesList, NodeRepr

def randid():
    return ''.join(random.choices('abcfghijklmopqrstuvwxyzABCFGHIJKLMOPQRSTUVWXYZ', k=6))


class StepperNode:
    def __init__(self, formula, children, satisfied, trace):
        self.children = children
        self.satisfied = satisfied
        
        self.trace = trace
        self.id = randid()
        self.formula = formula



    @property
    def treeAsMermaid(self):
        return self.__formula_to_mermaid__()

    @property
    def traceAsMermaid(self):
        return self.__trace_to_mermaid__()





    def __formula_to__mermaid_inner__(self):
        edges = []
        if self.satisfied:
            noderepr = f'{self.id}["{self.formula}"]:::satclass'
        else:
            noderepr = f'{self.id}[["{self.formula}"]]:::unsatclass'
        
        for child in self.children:
            child_repr = f'{child.id}["{child.formula}"]'
            edges.append(f'{noderepr}-->{child_repr}')

            child_edges = child.__formula_to__mermaid_inner__()
            edges += child_edges
        if len(edges) == 0:
            edges.append(noderepr)
        return edges

    def __formula_to_mermaid__(self):
        prefix = 'flowchart TD;\n'
        edges = self.__formula_to__mermaid_inner__()
        postfix = '\nclassDef unsatclass fill:#f96\nclassDef satclass fill:#008000'
        return prefix + ';'.join(edges) + postfix

    def __trace_to_mermaid__(self):


        def get_first_node_in_graph(edges):
            source_nodes = set(edge[0] for edge in graph_edges)
            destination_nodes = set(edge[1] for edge in graph_edges)
            root_nodes = source_nodes - destination_nodes
            ## if there are no root nodes, there is a problem!!
            return root_nodes.pop()

        graph_edges = mermaidFromSpotTrace(self.trace)
        g = mermaidGraphFromEdgesList(graph_edges)

        fn = get_first_node_in_graph(graph_edges)
        fnid = fn.id

        # Highlights the current state in the trace
        postfix = f"style {fnid} fill:#f9f,stroke:#333,stroke-width:4px"

        return g + postfix
        


class TraceSatisfactionResult:
    def __init__(self, prefix_states : list[StepperNode], cycle_states : list[StepperNode]):
        self.prefix_states = prefix_states
        self.cycle_states = cycle_states

    def to_dict(self):
        return {
            "prefix_states": self.prefix_states,
            "cycle_states": self.cycle_states
        }

    def __repr__(self):
        return f"TraceSatisfactionResult(prefix_states={self.prefix_states}, cycle_states={self.cycle_states})"


def satisfiesTrace(node, trace) -> StepperNode:

    formula = str(node)
    if trace == None or len(trace) == 0:
        return StepperNode(formula, [], True, trace)

    if isinstance(node, LiteralNode):
        return StepperNode(formula, [], is_trace_satisfied(formula=node, trace=trace), trace)
    elif isinstance(node, UnaryOperatorNode):
        return StepperNode(formula, [satisfiesTrace(node.operand, trace)], is_trace_satisfied(formula=node, trace=trace), trace)
    elif isinstance(node, BinaryOperatorNode):
        return StepperNode(formula, [satisfiesTrace(node.left, trace), satisfiesTrace(node.right, trace)], is_trace_satisfied(formula=node, trace=trace), trace)
    
    return StepperNode(formula, [], False, trace)


def buildNodeStep(node, subtrace, trace) -> StepperNode:
    stepperNode = satisfiesTrace(node = node, trace = subtrace)

    ### TODO: Over here:

    # Determine the first trace in the subtrace, and identify it as the current state
    # Then we build the trace in the overall trace, and identify the current state in the overall trace

    ### TODO: This needs to change to a more general approach
    # stepperNode.trace = trace
    # stepperNode.traceAsMermaid = stepperNode.__trace_to_mermaid__()

    return stepperNode




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
    if len(trace) == 0:
        return []
    
    prefix, cycle = splitTraceAtCycle(trace)


    def buildTraceForStateInPrefix(prefix_index):
        prefix_string = ';'.join(prefix[prefix_index:])

        if len(cycle) == 0:
            return prefix_string
        else:
            cycle_string = "cycle{" +  ';'.join(cycle) + "}"
            return prefix_string + ";" + cycle_string
        
        
    def buildTraceForStateInCycle(cycle_index):

        if len(cycle) == 0:
            return []
        
        ## Unroll one cycle, from the current state
        cycle_prefix_string = ';'.join(cycle[cycle_index:])
        if len(cycle_prefix_string) == 0:
            return []

        
        cycle_string = "cycle{" +  ';'.join(cycle) + "}"
        return cycle_prefix_string + ";" + cycle_string
    
    ## TODO: Is trace=trace correct here?
    prefix_sat = [buildNodeStep(node=node, subtrace=buildTraceForStateInPrefix(i), trace=trace) for i in range(len(prefix))]
    cycle_sat = [buildNodeStep(node=node, subtrace=buildTraceForStateInCycle(i), trace=trace) for i in range(len(cycle))]
    return TraceSatisfactionResult(prefix_sat, cycle_sat)
