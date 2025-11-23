import ltlnode
import random
import re

try:
    import inflect
    _inflect_engine = inflect.engine()
except ImportError:
    _inflect_engine = None

## We should list the various patterns of LTL formulae that we can handle

### What do we do about nested Globally and Finally nodes? ###

patterns = []
def pattern(func):
    patterns.append(func)
    return func


def clean_for_composition(english_text):
    """Helper function to clean English text for composition in patterns.
    
    Removes trailing periods and the first occurrence of ' holds' for cleaner phrasing.
    """
    text = english_text.rstrip('.')
    # Only remove the first ' holds' to avoid over-removal
    if ' holds' in text:
        text = text.replace(' holds', '', 1)
    return text


def join_with_conjunction(items, conj='and'):
    """Join items with proper grammar using inflect if available.
    
    Examples:
        ['p', 'q'] -> 'p and q'
        ['p', 'q', 'r'] -> 'p, q, and r'
    """
    if _inflect_engine:
        return _inflect_engine.join(items, conj=conj)
    # Fallback for when inflect is not available
    if len(items) == 0:
        return ''
    elif len(items) == 1:
        return items[0]
    elif len(items) == 2:
        return f'{items[0]} {conj} {items[1]}'
    else:
        return ', '.join(items[:-1]) + f', {conj} {items[-1]}'


def use_article(word):
    """Add appropriate article (a/an) before a word.
    
    Example: 'event' -> 'an event', 'state' -> 'a state'
    """
    if _inflect_engine:
        return _inflect_engine.a(word)
    # Simple fallback
    if word and len(word) > 0 and word[0].lower() in 'aeiou':
        return f'an {word}'
    return f'a {word}' if word else word


def capitalize_sentence(text):
    """Capitalize the first letter of a sentence.
    
    Handles edge cases like quoted literals at the start.
    
    Examples:
        'whenever p' -> 'Whenever p'
        "'p' holds" -> "'p' holds" (don't capitalize inside quotes)
        "at all times" -> "At all times"
    """
    if not text:
        return text
    
    # If text starts with a quote, don't capitalize the quoted content
    if text.startswith("'"):
        return text
    
    # Capitalize the first letter
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()


#### Globally special cases ####

# Pattern: G ( p -> (F q) )
# English, whenever p (holds), eventually q will (hold)
# Note: We check that left is not an UntilNode to allow more specific patterns to match first

@pattern
def response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            # Skip if left is Until - let more specific pattern handle it
            if type(left) is ltlnode.UntilNode:
                return None
            if type(right) is ltlnode.FinallyNode:
                left_eng = clean_for_composition(left.__to_english__())
                right_eng = clean_for_composition(right.operand.__to_english__())
                return f"whenever {left_eng}, eventually {right_eng}"
            
    return None


# Pattern G (F p)
# English: p (happens) repeatedly
# Note: Skip if inner is AndNode to let more specific patterns handle simultaneity
@pattern
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner_op = op.operand
            # Skip if inner is AndNode - let more specific pattern handle it
            if type(inner_op) is ltlnode.AndNode:
                return None
            inner_eng = clean_for_composition(inner_op.__to_english__())
            if type(inner_op) is ltlnode.LiteralNode:
                return f"{inner_eng} will happen infinitely often"
            return f"it is always the case that eventually {inner_eng}"
    return None


#### Final State Patterns ####

def _check_final_state_pattern(node, right_node_type):
    """Helper to check if a node matches the final state pattern G(p -> Op p).
    
    Args:
        node: The node to check
        right_node_type: The expected type for the right side operator (NextNode or GloballyNode)
    
    Returns:
        English translation if pattern matches, None otherwise
    """
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is right_node_type:
                # Check if both left and right.operand are literals with the same value
                if (type(left) is ltlnode.LiteralNode and
                    type(right.operand) is ltlnode.LiteralNode and
                    left.value == right.operand.value):
                    left_eng = clean_for_composition(left.__to_english__())
                    return f"once {left_eng}, it will always hold"
    return None


# Pattern: G (p -> X p)
# English: Once p (holds), it will always hold.
@pattern
def final_state_next_pattern(node):
    return _check_final_state_pattern(node, ltlnode.NextNode)


# Pattern: G (p -> G p)
# English: Once p (holds), it will always hold.
@pattern
def final_state_globally_pattern(node):
    return _check_final_state_pattern(node, ltlnode.GloballyNode)


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
                left_eng = clean_for_composition(left.__to_english__())
                lhs_eng = clean_for_composition(lhs.__to_english__())
                rhs_eng = clean_for_composition(rhs.__to_english__())
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
                    left_eng = clean_for_composition(left.__to_english__())
                    lhs_eng = clean_for_composition(lhs.operand.__to_english__())
                    rhs_eng = clean_for_composition(rhs.operand.__to_english__())
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
            negated_eng = clean_for_composition(negated.__to_english__())
            # For literals, use simpler phrasing
            if type(negated) is ltlnode.LiteralNode:
                return f"{negated_eng} will never occur"
            return f"it is never the case that {negated_eng}"


##### Finally special cases ####

# F ( !p )
# English: Eventually, it will not be the case that p (holds)
@pattern
def finally_not_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            negated_eng = clean_for_composition(op.operand.__to_english__())
            # For literals, simpler phrasing
            if type(op.operand) is ltlnode.LiteralNode:
                return f"eventually, not {negated_eng}"
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
                negated_eng = clean_for_composition(negated.operand.__to_english__())
                return f"eventually, {negated_eng} will never occur again"
    return None


# F (G p)
# English: Eventually, p will always (hold)
# Note: Skip if inner is an ImpliesNode with Finally on right - let more specific pattern handle it
@pattern
def finally_globally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            inner = op.operand
            # Skip if inner is implication with Finally - let more specific pattern handle it
            if type(inner) is ltlnode.ImpliesNode and type(inner.right) is ltlnode.FinallyNode:
                return None
            inner_eng = clean_for_composition(inner.__to_english__())
            return f"eventually, {inner_eng} will always be true"
    return None


# F (p & q)
# English: Eventually at the same time, p and q will (hold)
@pattern
def finally_and_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            return f"eventually, both {left_eng} and {right_eng} will be true simultaneously"
    return None

# ! (F p)
# English: It will never be the case that p (holds)
@pattern
def not_finally_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner_eng = clean_for_composition(op.operand.__to_english__())
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
            p_eng = clean_for_composition(left.left.__to_english__())
            q_eng = clean_for_composition(left.right.__to_english__())
            r_eng = clean_for_composition(right.__to_english__())
            return f"{p_eng} until {q_eng}, and this continues until {r_eng}"
    return None


#### Context-aware patterns for nested temporal operators ####
# These patterns help address deictic shift issues where temporal references can be ambiguous

# Pattern: G(F(p & q))
# English: at all times, there will eventually be a point where both p and q hold simultaneously
@pattern
def globally_finally_and_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner = op.operand
            if type(inner) is ltlnode.AndNode:
                left_eng = clean_for_composition(inner.left.__to_english__())
                right_eng = clean_for_composition(inner.right.__to_english__())
                return f"at all times, there will eventually be a point where both {left_eng} and {right_eng} hold simultaneously"
    return None


# Pattern: F(G(p -> F q))
# English: eventually we reach a point where, from then on, whenever p then eventually q
@pattern
def finally_globally_implies_finally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            inner = op.operand
            if type(inner) is ltlnode.ImpliesNode:
                if type(inner.right) is ltlnode.FinallyNode:
                    left_eng = clean_for_composition(inner.left.__to_english__())
                    right_eng = clean_for_composition(inner.right.operand.__to_english__())
                    return f"eventually we reach a point where, from then on, whenever {left_eng} then eventually {right_eng}"
    return None


# Pattern: (G p) U (F q)
# English: at all times p holds, and this continues until eventually q occurs
@pattern
def globally_until_finally_pattern_to_english(node):
    if type(node) is ltlnode.UntilNode:
        left = node.left
        right = node.right
        if type(left) is ltlnode.GloballyNode and type(right) is ltlnode.FinallyNode:
            left_eng = clean_for_composition(left.operand.__to_english__())
            right_eng = clean_for_composition(right.operand.__to_english__())
            return f"at all times {left_eng}, and this continues until eventually {right_eng} occurs"
    return None


# Pattern: X(p U q)
# English: in the next step, p until q
@pattern
def next_until_pattern_to_english(node):
    if type(node) is ltlnode.NextNode:
        op = node.operand
        if type(op) is ltlnode.UntilNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            return f"in the next step, {left_eng} until {right_eng}"
    return None


# Pattern: G((p U q) -> F r)
# English: whenever p until q, eventually r will occur
@pattern
def globally_until_implies_finally_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(left) is ltlnode.UntilNode and type(right) is ltlnode.FinallyNode:
                p_eng = clean_for_composition(left.left.__to_english__())
                q_eng = clean_for_composition(left.right.__to_english__())
                r_eng = clean_for_composition(right.operand.__to_english__())
                return f"whenever {p_eng} until {q_eng}, eventually {r_eng} will occur"
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
        inner_eng = clean_for_composition(node.__to_english__())
        return f"in {number_of_nexts} steps, {inner_eng}"
    return None


def apply_special_pattern_if_possible(node):

    for pattern in patterns:
        result = pattern(node)
        if result is not None:
            return capitalize_sentence(result)
    return None




#import language_tool_python


def correct_grammar(text):
    return text

    # with language_tool_python.LanguageTool('en-US') as languageTool:
    #     corrected_text = languageTool.correct(text)

    # ## Now, if any text is in single quotes, make it lowecase
    # corrected_text = re.sub(r"'(.*?)'", lambda x: f"'{x.group(1).lower()}'", corrected_text)
    # return corrected_text
