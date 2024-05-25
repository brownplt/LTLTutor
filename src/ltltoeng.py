import ltlnode
import random

## We should list the various patterns of LTL formulae that we can handle






#### Globally special cases ####

# Pattern: G ( p -> (F q) )
# English, whenever p (holds), eventually q will (hold)

def response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.FinallyNode:
                return "whenever " + left.__to_english__() + ", eventually " + right.operand.__to_english__()
            
    return None


# Pattern G (F p)
# English: p (happens) repeatedly TODO: Think about how to properly phrase this
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            return "It is repeatedly the case that " + op.operand.__to_english__()
    return None


## Chain precedence
# Pattern G(p -> (X (q U r)))
# English: Whenever p (happens), q will (hold) until r (holds)

def chain_precedence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
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
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.AndNode:
                lhs = right.left
                rhs = right.right
                if type(lhs) is ltlnode.FinallyNode and type(rhs) is ltlnode.FinallyNode:
                    return "whenever " + left.__to_english__() + ", eventually" + lhs.operand.__to_english__() + " and " + rhs.operand.__to_english__() 
    return None


##### Finally special cases ####

# F (!p) 
# English: Eventually, it will never be the case that p (holds)
def finally_not_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            return "eventually, it will never be the case that " + op.operand.__to_english__()
    return None

# F (p & q)
# English: Eventually at the same time, p and q will (hold)
def finally_and_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            return "eventually at the same time, " + op.left.__to_english__() + " and " + op.right.__to_english__()
    return None

### Until special cases ###

# (p U q) U r
# English: p will (hold) until q (holds), and this will continue until r (holds)
def nested_until_pattern_to_english(node):
    if type(node) is ltlnode.UntilNode:
        left = node.left
        right = node.right
        if type(left) is ltlnode.UntilNode:
            return "it will be the case that " + left.left.__to_english__() + " until " + left.right.__to_english__() + ", and this will continue until " + right.__to_english__()
    return None



patterns = [
    response_pattern_to_english,
    recurrence_pattern_to_english,
    chain_precedence_pattern_to_english,
    chain_response_pattern_to_english,
    finally_not_pattern_to_english,
    finally_and_pattern_to_english,
    nested_until_pattern_to_english
]


def apply_special_pattern_if_possible(node):
    #random.shuffle(patterns)
    for pattern in patterns:
        result = pattern(node)
        if result is not None:
            print("Pattern matched: " + str(result))
            return result
    
    print("No pattern matched for node: " + str(node) + " of type: " + str(type(node)) + " returning None)")
    return None