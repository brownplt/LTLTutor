import ltlnode

## We should list the various patterns of LTL formulae that we can handle


#### Globally special cases ####

# Pattern: G ( p -> (F q) )
# English, whenever p (holds), eventually q will (hold)

def response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImplicationNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.EventuallyNode:
                return "whenever " + left.__to_english__() + ", eventually " + right.operand.__to_english__()
            
    return None


# Pattern G (F p)
# English: p (happens) repeatedly TODO: Think about how to properly phrase this
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.EventuallyNode:
            return op.operand.__to_english__() + " repeatedly"
    return None


## Chain precedence
# Pattern G(p -> (X (q U r)))
# English: Whenever p (happens), q will (hold) until r (holds)

def chain_precedence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImplicationNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.UntilNode:
                lhs = right.left
                rhs = right.right
                return "whenever " + left.__to_english__() + ", " + lhs.__to_english__() + " until " + rhs.__to_english__()
    return None


## Chain response
# Pattern: G (p -> ( (F q) & (F r) ) )
# English: Whenever p (holds), q and r will (hold) eventually
def chain_response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImplicationNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.AndNode:
                lhs = right.left
                rhs = right.right
                if type(lhs) is ltlnode.EventuallyNode and type(rhs) is ltlnode.EventuallyNode:
                    return "whenever " + left.__to_english__() + ", eventually" + lhs.operand.__to_english__() + " and " + rhs.operand.__to_english__() 
    return None