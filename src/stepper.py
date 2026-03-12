from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode, parse_ltl_string
import ltltoeng
from spotutils import is_trace_satisfied
import re
import random
import html as html_module
from exerciseprocessor import NodeRepr

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
        return ltltoeng.finalize_sentence(node.__to_english__())

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
    def formulaAsHTML(self):
        return self.__formula_to_html__()

    @property
    def formattedTraceAssignment(self):
        asStr = self.traceAssignmentStr
        asStr = asStr.replace('&', '\u2003')
        asStr = asStr.replace('! ', '!')
        asStr = asStr.replace('!', '¬')
        return asStr

    @property
    def formulaTreeAsHTML(self):
        return f'<ul class="formula-tree">{self._build_tree_html()}</ul>'

    def _build_tree_html(self):
        sat_class = "tree-sat" if self.satisfied else "tree-unsat"
        escaped = html_module.escape(self.formula)
        children_html = ""
        if self.children:
            items = "".join(c._build_tree_html() for c in self.children)
            children_html = f'<ul>{items}</ul>'
        return f'<li class="{sat_class}"><code>{escaped}</code>{children_html}</li>'

    def getAllSubformulae(self):
        """Extract all subformulae from this node and its children recursively."""
        result = [(self.formula, self.satisfied)]
        for child in self.children:
            result.extend(child.getAllSubformulae())
        return result


    # And hopefully satclass and unsatclass are things in the CSS

    ### Hacky, we should improve this via tree parsing or something?
    ### THis approach doesn't work I think :(
    ## Like LTL Node to HTML
    def __formula_to_html__(self):
        formula_html = self.formula

        # Sort children by length (longest first) to avoid partial overlaps
        for child in sorted(self.children, key=lambda c: -len(c.formula)):
            if '(' in child.formula or ')' in child.formula:
                # Use full replace for formulas with parentheses
                pattern = re.escape(child.formula)
            else:
                # Use word boundary for simple formulas
                pattern = r'\b{}\b'.format(re.escape(child.formula))
            replacement = child.__formula_to_html__()
            formula_html = re.sub(pattern, replacement, formula_html)

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
    
    def getMatrixView(self):
        """Generate matrix view data for table display."""
        all_states = self.prefix_states + self.cycle_states
        
        if not all_states:
            return {"subformulae": [], "matrix": [], "rows": []}
        
        # Collect all unique subformulae across all states
        all_subformulae_set = set()
        for state in all_states:
            subformulae = state.getAllSubformulae()
            for formula, _ in subformulae:
                all_subformulae_set.add(formula)
        
        # Sort subformulae for consistent ordering (simple ones first, complex ones last)
        all_subformulae = sorted(list(all_subformulae_set), key=lambda x: (len(x), x))
        
        # Build matrix: rows are subformulae, columns are time steps
        matrix = []
        rows = []  # Combined data for easier template iteration
        for subformula in all_subformulae:
            row = []
            for state in all_states:
                # Find this subformula in the current state
                subformulae = state.getAllSubformulae()
                subformula_dict = {f: s for f, s in subformulae}
                satisfaction = subformula_dict.get(subformula, False)
                row.append(1 if satisfaction else 0)
            matrix.append(row)
            rows.append({"subformula": subformula, "values": row})
        
        return {
            "subformulae": all_subformulae,
            "matrix": matrix,
            "rows": rows
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


def getTraceRenderData(trace):
    """Build structured trace data for the client-side SVG trace renderer."""
    prefix, cycle = splitTraceAtCycle(trace)

    def fmt(s):
        s = s.replace('&', '\u2003')
        s = s.replace('! ', '!')
        s = s.replace('!', '\u00ac')
        return s.strip()

    return {
        "prefix": [{"label": fmt(s)} for s in prefix],
        "cycle": [{"label": fmt(s)} for s in cycle]
    }
