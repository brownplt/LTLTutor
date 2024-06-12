
from ltlnode import UnaryOperatorNode, BinaryOperatorNode, LiteralNode
from spotutils import is_trace_satisfied



class StepperNode:
    def __init__(self, children, satisfied, trace):
        self.children = children
        self.satisfied = satisfied
        self.trace = trace


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


# Trace has to be a list of spot word formulae
def traceSatisfactionPerStep(node, trace):
    if len[trace] == 0:
        return []
    
    ## TODO: What about cycles ##
    return [satisfiesTrace(node, trace[i:]) for i in range(len(trace))]



## TODO: Write a procedure to convert a spot trace to a list of individual states (including cycles)
## How do we step within cycles. Should be solvable, just need to think about it.