from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode, parse_ltl_string
from spotutils import is_trace_satisfied
import re
import random
from exerciseprocessor import mermaidFromSpotTrace, mermaidGraphFromEdgesList, NodeRepr

def randid():
    return ''.join(random.choices('abcfghijklmopqrstuvwxyzABCFGHIJKLMOPQRSTUVWXYZ', k=6))



def getLTLFormulaAsString(node, syntax):


    ## Check if node is a string ##
    if isinstance(node, str):
        node = parse_ltl_string(node)


    if syntax == "Classic":
        return str(node)
    elif syntax == "Forge":
        return node.__forge__()
    elif syntax == "Electrum":
        return node.__electrum__()
    elif syntax == "English":
        ## We should hopefully never get here. However, 
        ## I'm adding it here to suggest a way forward.
        return node.__to_english__()

    ## Default to classic syntax
    return str(node)

class StepperNode:
    def __init__(self, formula, children, satisfied, trace, traceindex, originaltrace):
        self.children = children
        self.satisfied = satisfied
        
        self.trace = trace
        self.id = randid()
        self.formula = formula
        self.traceindex = traceindex
        self.originaltrace = originaltrace

        # Set traceAssignmentStr to everything in trace UNTIL the first ';', with 'cycle{' removed if present
        if trace:
            first_part = trace.split(';', 1)[0].replace('cycle{', '').strip()
            self.traceAssignmentStr = first_part
        else:
            self.traceAssignmentStr = ""

    @property
    def treeAsMermaid(self):
        return self.__formula_to_mermaid__()

    @property
    def traceAsMermaid(self):
        return self.__trace_to_mermaid__()


    @property
    def formulaAsHTML(self):
        return self.__formula_to_html__()

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
        postfix = '\nclassDef unsatclass stroke:#f96,stroke-width:2px\nclassDef satclass stroke:#008000,stroke-width:2px;'
        return prefix + ';'.join(edges) + postfix

    def __trace_to_mermaid__(self):


        def get_nth_node_in_graph(edges, n):
            # Find the root node
            source_nodes = set(edge[0] for edge in edges)
            destination_nodes = set(edge[1] for edge in edges)
            root_nodes = source_nodes - destination_nodes


            # If there is no root node, the graph is cyclic
            # then, the root node is the first node in the graph
            if len(root_nodes) == 0:
                current_node = edges[0][0]
            else:
                current_node = root_nodes.pop()

            # Follow the edges from the root node
            for _ in range(n):
                for edge in edges:
                    if edge[0] == current_node:
                        current_node = edge[1]
                        break
                else:
                    raise IndexError('Node index out of range')
            
            return current_node

        graph_edges = mermaidFromSpotTrace(self.originaltrace)



        g = mermaidGraphFromEdgesList(graph_edges)

   
        fn = get_nth_node_in_graph(graph_edges, self.traceindex)
        fnid = fn.id

        # Highlights the current state in the trace
        postfix = f"style {fnid} stroke:#333,stroke-width:4px"

        return g + postfix
        

    # And hopefully satclass and unsatclass are things in the CSS
    def __formula_to_html__(self):
        formula_html = self.formula

        # Replace only the first occurrence of each child formula, outside of HTML tags
        for child in self.children:
            # Escape special regex characters in the formula
            pattern = r'\b{}\b'.format(re.escape(child.formula))
            replacement = child.__formula_to_html__()

            # Replace only outside of tags
            def replacer(match):
                # Check if we're inside a tag (very basic check)
                before = formula_html[:match.start()]
                if before.endswith('>'):
                    return match.group(0)  # Don't replace inside tags
                return replacement

            # Only replace the first occurrence
            formula_html, count = re.subn(pattern, replacer, formula_html, count=1)

        if self.satisfied:
            return f'<span class="satformula">{formula_html}</span>'
        else:
            return f'<span class="unsatformula">{formula_html}</span>'


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




def satisfiesTrace(node, trace, traceindex, originaltrace, syntax) -> StepperNode:

    formula = str(node)
    formula_as_string = getLTLFormulaAsString(node, syntax)


    ### StepperNode(self, formula, children, satisfied, trace, traceindex, originaltrace):
    if trace == None or len(trace) == 0:
        return StepperNode(formula_as_string, [], True, trace, traceindex=traceindex, originaltrace=originaltrace)

    if isinstance(node, LiteralNode):
        return StepperNode(formula_as_string, [], is_trace_satisfied(formula=node, trace=trace), trace, traceindex=traceindex, originaltrace=originaltrace)
    elif isinstance(node, UnaryOperatorNode):
        return StepperNode(formula_as_string, 
                           [satisfiesTrace(node.operand, trace,  traceindex=traceindex, originaltrace=originaltrace,syntax=syntax)],
                            is_trace_satisfied(formula=node, trace=trace),
                            trace,
                            traceindex=traceindex,
                            originaltrace=originaltrace)
    elif isinstance(node, BinaryOperatorNode):
        return StepperNode(formula_as_string, 
                           [ satisfiesTrace(node.left, trace,  traceindex=traceindex, originaltrace=originaltrace, syntax=syntax),
                             satisfiesTrace(node.right, trace,  traceindex=traceindex, originaltrace=originaltrace, syntax=syntax)],
                            is_trace_satisfied(formula=node, trace=trace),
                            trace, 
                            traceindex=traceindex, 
                            originaltrace=originaltrace)
    
    return StepperNode(formula, [], False, trace, traceindex=traceindex, originaltrace=originaltrace)


def buildNodeStep(node, subtrace, trace_index_of_subtrace, trace, syntax) -> StepperNode:
    stepperNode = satisfiesTrace(node = node, trace = subtrace, traceindex=trace_index_of_subtrace, originaltrace=trace, syntax = syntax)

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
def traceSatisfactionPerStep(node, trace, syntax):
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
    
    num_prefix_states = len(prefix)
    prefix_sat = [buildNodeStep(node=node, subtrace=buildTraceForStateInPrefix(i), trace=trace, trace_index_of_subtrace=i, syntax=syntax) for i in range(len(prefix))]


    cycle_sat = [buildNodeStep(node=node, subtrace=buildTraceForStateInCycle(i), trace=trace, trace_index_of_subtrace= num_prefix_states + i, syntax=syntax) for i in range(len(cycle))]
    return TraceSatisfactionResult(prefix_sat, cycle_sat)
