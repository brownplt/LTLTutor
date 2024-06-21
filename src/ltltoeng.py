import ltlnode
import random
import re

## We should list the various patterns of LTL formulae that we can handle

### What do we do about nested Globally and Finally nodes? ###

patterns = []
def pattern(func):
    patterns.append(func)
    return func


#### Globally special cases ####

# Pattern: G ( p -> (F q) )
# English, whenever p (holds), eventually q will (hold)

@pattern
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
@pattern
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:

            inner_op = op.operand
            if type(inner_op) is ltlnode.LiteralNode:
                return f"'{inner_op.value}' will repeatedly hold"
            return "there will always be a point in the future where " + op.operand.__to_english__()
    return None


## Chain precedence
# Pattern G(p -> (X (q U r)))
# English: Whenever p (happens), q will (hold) until r (holds)

@pattern
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
@pattern
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


## G !p
# English: It will never be the case that p (holds)
@pattern
def never_globally_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:

            negated = op.operand
            if type(negated) is ltlnode.LiteralNode:
                return f"'{negated.value}' will never hold"

            return "it will never be the case that " + op.operand.__to_english__()


##### Finally special cases ####

# F ( !p )
# English: Eventually, it will not be the case that p (holds)
@pattern
def finally_not_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            return "eventually, it will not be the case that " + op.operand.__to_english__()
    return None


# F (G !p)
# English: Eventually, it will never be the case that p (holds)
@pattern
def finally_never_globally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            negated = op.operand
            if type(negated) is ltlnode.NotNode:
                return "eventually, it will never be the case that " + negated.operand.__to_english__()
    return None


# F (G p)
# English: Eventually, p will always (hold)
@pattern
def finally_globally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            return "eventually, it will always be the case that " + op.operand.__to_english__() 
    return None


# F (p & q)
# English: Eventually at the same time, p and q will (hold)
@pattern
def finally_and_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            return "eventually at the same time, " + op.left.__to_english__() + " and " + op.right.__to_english__()
    return None

# ! (F p)
# English: It will never be the case that p (holds)
@pattern
def not_finally_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            return "it will never be the case that " + op.operand.__to_english__()
    return None

### Until special cases ###

# (p U q) U r
# English: p will (hold) until q (holds), and this will continue until r (holds)
@pattern
def nested_until_pattern_to_english(node):
    if type(node) is ltlnode.UntilNode:
        left = node.left
        right = node.right
        if type(left) is ltlnode.UntilNode:
            return "it will be the case that " + left.left.__to_english__() + " until " + left.right.__to_english__() + ", and this will continue until " + right.__to_english__()
    return None

#### neXt special cases ####

# X X X X r
# English: In _n_ states, r will (hold)
@pattern
def apply_next_special_pattern_if_possible(node):

    number_of_nexts = 0

    while type(node) is ltlnode.NextNode:
        number_of_nexts += 1
        node = node.operand

    if number_of_nexts > 1:
        return "in " + str(number_of_nexts) + " states, " + node.__to_english__()
    return None


def apply_special_pattern_if_possible(node):

    for pattern in patterns:
        result = pattern(node)
        if result is not None:
            return result
    return None




#import language_tool_python


def correct_grammar(text):
    return text
    ## TODO: Correcting an issue here
    # blob = TextBlob(text)
    # corrected_text = str(blob.correct())
    # languageTool = language_tool_python.LanguageTool('en-US')
    # corrected_text = languageTool.correct(text)

    ## Now, if any text is in single quotes, make it lowecase
    corrected_text = re.sub(r"'(.*?)'", lambda x: f"'{x.group(1).lower()}'", corrected_text)
    return corrected_text
