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
                left_eng = left.__to_english__()
                right_eng = right.operand.__to_english__()
                # Remove trailing "holds" for cleaner composition
                left_eng = left_eng.rstrip('.').replace(" holds", "", 1) if " holds" in left_eng else left_eng
                right_eng = right_eng.rstrip('.').replace(" holds", "", 1) if " holds" in right_eng else right_eng
                return f"whenever {left_eng}, eventually {right_eng}"
            
    return None


# Pattern G (F p)
# English: p (happens) repeatedly
@pattern
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner_op = op.operand
            inner_eng = inner_op.__to_english__()
            # Remove "holds" for cleaner phrasing
            inner_eng = inner_eng.rstrip('.').replace(" holds", "", 1) if " holds" in inner_eng else inner_eng
            if type(inner_op) is ltlnode.LiteralNode:
                return f"{inner_eng} will happen infinitely often"
            return f"it is always the case that eventually {inner_eng}"
    return None


## Chain precedence
# Pattern G(p -> (q U r))
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
                left_eng = left.__to_english__().rstrip('.')
                lhs_eng = lhs.__to_english__().rstrip('.')
                rhs_eng = rhs.__to_english__().rstrip('.')
                # Remove "holds" for cleaner composition
                left_eng = left_eng.replace(" holds", "", 1) if " holds" in left_eng else left_eng
                lhs_eng = lhs_eng.replace(" holds", "", 1) if " holds" in lhs_eng else lhs_eng
                rhs_eng = rhs_eng.replace(" holds", "", 1) if " holds" in rhs_eng else rhs_eng
                return f"whenever {left_eng}, {lhs_eng} until {rhs_eng}"
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
                    left_eng = left.__to_english__().rstrip('.')
                    lhs_eng = lhs.operand.__to_english__().rstrip('.')
                    rhs_eng = rhs.operand.__to_english__().rstrip('.')
                    # Remove "holds" for cleaner composition
                    left_eng = left_eng.replace(" holds", "", 1) if " holds" in left_eng else left_eng
                    lhs_eng = lhs_eng.replace(" holds", "", 1) if " holds" in lhs_eng else lhs_eng
                    rhs_eng = rhs_eng.replace(" holds", "", 1) if " holds" in rhs_eng else rhs_eng
                    return f"whenever {left_eng}, eventually {lhs_eng} and {rhs_eng}"
    return None


## G !p
# English: It will never be the case that p (holds)
@pattern
def never_globally_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            negated = op.operand
            negated_eng = negated.__to_english__().rstrip('.')
            # For literals, use simpler phrasing
            if type(negated) is ltlnode.LiteralNode:
                return f"{negated_eng.replace(' holds', '')} will never occur"
            # Remove "holds" for cleaner composition
            negated_eng = negated_eng.replace(" holds", "", 1) if " holds" in negated_eng else negated_eng
            return f"it is never the case that {negated_eng}"


##### Finally special cases ####

# F ( !p )
# English: Eventually, it will not be the case that p (holds)
@pattern
def finally_not_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            negated_eng = op.operand.__to_english__().rstrip('.')
            # For literals, simpler phrasing
            if type(op.operand) is ltlnode.LiteralNode:
                return f"eventually, not {negated_eng}"
            # Remove "holds" for cleaner composition
            negated_eng = negated_eng.replace(" holds", "", 1) if " holds" in negated_eng else negated_eng
            return f"eventually, it will not be the case that {negated_eng}"
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
                negated_eng = negated.operand.__to_english__().rstrip('.')
                # Remove "holds" for cleaner composition
                negated_eng = negated_eng.replace(" holds", "", 1) if " holds" in negated_eng else negated_eng
                return f"eventually, {negated_eng} will never occur again"
    return None


# F (G p)
# English: Eventually, p will always (hold)
@pattern
def finally_globally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            inner_eng = op.operand.__to_english__().rstrip('.')
            # Remove "holds" for cleaner composition
            inner_eng = inner_eng.replace(" holds", "", 1) if " holds" in inner_eng else inner_eng
            return f"eventually, {inner_eng} will always be true"
    return None


# F (p & q)
# English: Eventually at the same time, p and q will (hold)
@pattern
def finally_and_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            left_eng = op.left.__to_english__().rstrip('.')
            right_eng = op.right.__to_english__().rstrip('.')
            # Remove "holds" for cleaner composition
            left_eng = left_eng.replace(" holds", "", 1) if " holds" in left_eng else left_eng
            right_eng = right_eng.replace(" holds", "", 1) if " holds" in right_eng else right_eng
            return f"eventually, both {left_eng} and {right_eng} will be true simultaneously"
    return None

# ! (F p)
# English: It will never be the case that p (holds)
@pattern
def not_finally_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner_eng = op.operand.__to_english__().rstrip('.')
            # Remove "holds" for cleaner composition
            inner_eng = inner_eng.replace(" holds", "", 1) if " holds" in inner_eng else inner_eng
            return f"{inner_eng} will never occur"
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
            p_eng = left.left.__to_english__().rstrip('.')
            q_eng = left.right.__to_english__().rstrip('.')
            r_eng = right.__to_english__().rstrip('.')
            # Remove "holds" for cleaner composition
            p_eng = p_eng.replace(" holds", "", 1) if " holds" in p_eng else p_eng
            q_eng = q_eng.replace(" holds", "", 1) if " holds" in q_eng else q_eng
            r_eng = r_eng.replace(" holds", "", 1) if " holds" in r_eng else r_eng
            return f"{p_eng} until {q_eng}, and this continues until {r_eng}"
    return None

#### neXt special cases ####

# X X X X r
# English: In _n_ states, r will (hold)
@pattern
def apply_next_special_pattern_if_possible(node):

    number_of_nexts = 0
    original_node = node

    while type(node) is ltlnode.NextNode:
        number_of_nexts += 1
        node = node.operand

    if number_of_nexts > 1:
        inner_eng = node.__to_english__().rstrip('.')
        # Remove "holds" for cleaner composition
        inner_eng = inner_eng.replace(" holds", "", 1) if " holds" in inner_eng else inner_eng
        return f"in {number_of_nexts} steps, {inner_eng}"
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

    # with language_tool_python.LanguageTool('en-US') as languageTool:
    #     corrected_text = languageTool.correct(text)

    # ## Now, if any text is in single quotes, make it lowecase
    # corrected_text = re.sub(r"'(.*?)'", lambda x: f"'{x.group(1).lower()}'", corrected_text)
    # return corrected_text
