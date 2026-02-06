import ltlnode
import ltlir
import random
import re

import inflect
from wordfreq import zipf_frequency

_inflect_engine = inflect.engine()

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


def _steps_phrase(count):
    """Return a human-friendly description like 'two steps'."""
    if count == 1:
        return "1 step"
    if _inflect_engine:
        return f"{_inflect_engine.number_to_words(count)} steps"
    return f"{count} steps"


def _count_next_chain(node):
    """Count consecutive Next nodes and return (count, innermost operand)."""
    steps = 0
    while type(node) is ltlnode.NextNode:
        steps += 1
        node = node.operand
    return steps, node


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
    
    # Clean up any double spaces or whitespace issues
    text = ' '.join(text.split())
    
    # If text starts with a quote, don't capitalize the quoted content
    if text.startswith("'"):
        return text
    
    # Capitalize the first letter
    return text[0].upper() + text[1:] if len(text) > 1 else text.upper()


def smooth_grammar(text):
    """Apply grammar smoothing rules to improve readability.

    Fixes common awkward phrasings that arise from composition.
    """
    if not text:
        return text
    
    # Fix "both both" -> "both"
    text = text.replace("both both", "both")
    
    # Fix "either either" -> "either"  
    text = text.replace("either either", "either")
    
    # Fix "not not" -> "" (double negation in text)
    text = text.replace("not not ", "")
    
    # Fix "if if" -> "if"
    text = text.replace("if if", "if")
    
    # Fix "then then" -> "then"
    text = text.replace("then then", "then")
    
    # Fix "hold hold" or "holds holds" -> "hold" or "holds"
    text = text.replace("hold hold", "hold")
    text = text.replace("holds holds", "holds")
    
    # Fix awkward "it is the case that it is the case that"
    text = text.replace("it is the case that it is the case that", "it is the case that")
    
    # Fix "it is not the case that it is not the case that" -> ""
    text = text.replace("it is not the case that it is not the case that", "")
    
    # Fix ", ," -> ","
    text = text.replace(", ,", ",")

    # Remove redundant "the case where" before "until" (e.g., "or the case where p until q" -> "or p until q")
    # This handles patterns like "!p1 | (p0 U p2)" -> "either p1 is false or p0 until p2"
    text = re.sub(r'\b(either|or|and|both)\s+the case where\s+(\S.*?\s+until\s+)', r'\1 \2', text, flags=re.IGNORECASE)
    
    # Remove redundant "the state that" before "until" 
    text = re.sub(r'\b(either|or|and|both)\s+the state that\s+(\S.*?\s+holds\s+until\s+)', r'\1 \2', text, flags=re.IGNORECASE)
    
    # Simplify "either X or the case where Y" -> "either X or Y" when Y is already a clause
    text = re.sub(r'\b(either\s+[^,]+)\s+or\s+the case where\s+', r'\1 or ', text, flags=re.IGNORECASE)

    # Normalize mid-sentence capitalization of connectives like "If" or "Then"
    def _lowercase_mid_sentence(match):
        return match.group(1).lower()

    text = re.sub(r"(?<!^)(?<![.!?]\s)(\b(?:If|Then|When|Whenever|Where|Unless|Until|Not|Neither|Either|Both|Always|Eventually|At)\b)",
                  _lowercase_mid_sentence,
                  text)

    # Fix double spaces
    text = ' '.join(text.split())

    return text


def normalize_embedded_clause(text):
    """Make a composed clause read naturally inside a larger sentence.
    
    - Lowercase the leading word when it is embedded mid-sentence.
    - Append 'holds' after bare literals that lack a verb.
    """
    if not text:
        return text

    t = text.strip()

    # Append 'holds' if this looks like a bare literal and doesn't already have a verb
    if t.startswith("'") and "hold" not in t:
        t = f"{t} holds"

    # Lowercase initial letter when not quoted (embedded clause)
    if t and not t.startswith("'") and t[0].isupper():
        t = t[0].lower() + t[1:]

    return t


def finalize_sentence(text):
    """Apply smoothing and capitalization once, at the top level."""
    if text is None:
        return ""
    smoothed = smooth_grammar(text.strip())
    return capitalize_sentence(smoothed)


def _embedded_clause(node):
    """Return a clause suitable for embedding after a discourse prefix."""
    text = clean_for_composition(node.__to_english__())
    return normalize_embedded_clause(text)


def _node_size(node):
    if isinstance(node, ltlnode.UnaryOperatorNode):
        return 1 + _node_size(node.operand)
    if isinstance(node, ltlnode.BinaryOperatorNode):
        return 1 + _node_size(node.left) + _node_size(node.right)
    return 1


def _temporal_op_count(node):
    count = 0
    if isinstance(node, (ltlnode.NextNode, ltlnode.FinallyNode, ltlnode.GloballyNode, ltlnode.UntilNode)):
        count += 1
    if isinstance(node, ltlnode.UnaryOperatorNode):
        return count + _temporal_op_count(node.operand)
    if isinstance(node, ltlnode.BinaryOperatorNode):
        return count + _temporal_op_count(node.left) + _temporal_op_count(node.right)
    return count


def _should_split_conjunction(node):
    if not isinstance(node, (ltlnode.AndNode, ltlnode.OrNode)):
        return False
    left_ops = _temporal_op_count(node.left)
    right_ops = _temporal_op_count(node.right)
    total_ops = left_ops + right_ops
    total_size = _node_size(node)
    return total_ops >= 2 or total_size >= 8


def _eventual_anchor_phrasing():
    return (
        choose_best_sentence([
            "eventually we reach a point in time",
            "eventually there is a point in time",
            "eventually a point is reached"
        ]),
        "from then on"
    )


def build_discourse_plan(node):
    """Compile select LTL forms into a discourse-oriented plan."""
    # Eventual permanence: F(G φ) -> anchor + "from then on" clause
    if isinstance(node, ltlnode.FinallyNode) and isinstance(node.operand, ltlnode.GloballyNode):
        anchor_sentence, prefix = _eventual_anchor_phrasing()
        inner = node.operand.operand
        plan = ltlir.TemporalPlan()
        plan.add_anchor(anchor_sentence)
        plan.add_clause(_embedded_clause(inner), prefix=prefix)
        return plan

    # Split large conjunctions into two sentences
    if isinstance(node, ltlnode.AndNode) and _should_split_conjunction(node):
        plan = ltlir.TemporalPlan()
        plan.add_lead("both of the following must hold")
        plan.add_clause(_embedded_clause(node.left), prefix="first")
        plan.add_clause(_embedded_clause(node.right), prefix="second")
        return plan

    # Split large disjunctions into two sentences
    if isinstance(node, ltlnode.OrNode) and _should_split_conjunction(node):
        plan = ltlir.TemporalPlan()
        plan.add_lead("at least one of the following must hold")
        left_clause = _embedded_clause(node.left)
        right_clause = _embedded_clause(node.right)
        plan.add_clause(f"either {left_clause} or {right_clause}")
        return plan

    return None


def render_discourse_plan(plan):
    sentences = []
    for step in plan.steps:
        text = step.text
        if step.prefix:
            text = f"{step.prefix}, {text}"
        sentence = finalize_sentence(text)
        if sentence:
            sentences.append(sentence)
    return ". ".join(sentences)


def to_english_discourse(node):
    plan = build_discourse_plan(node)
    if plan:
        return render_discourse_plan(plan)
    return finalize_sentence(node.__to_english__())


def translate(node, discourse=False):
    """Top-level translation entrypoint with optional discourse planning."""
    if discourse:
        return to_english_discourse(node)
    return finalize_sentence(node.__to_english__())


def _ngram_fluency_score(text):
    """Lightweight fluency score using token and bi-gram heuristics.
    
    The goal is to pick the most natural-sounding option from a small
    candidate set, not to be a full language model.
    """
    if not text:
        return float("-inf")

    normalized = text.lower()
    tokens = re.findall(r"[a-z']+", normalized)
    if not tokens:
        return float("-inf")

    # Encourage concise phrasing; small penalty per token
    score = -0.05 * len(tokens)

    # Penalize repeated consecutive words (kept minimal for clarity)
    for i in range(1, len(tokens)):
        if tokens[i] == tokens[i - 1]:
            score -= 0.5

    bigrams = list(zip(tokens, tokens[1:]))

    # Mild penalty for overusing "holds"
    score -= 0.1 * normalized.count("holds")

    # Frequency-based fluency cues using pre-built Zipf estimates
    token_freq_score = sum(zipf_frequency(tok, 'en') for tok in tokens) / len(tokens)
    score += 0.2 * token_freq_score

    if bigrams:
        bigram_scores = [zipf_frequency(' '.join(bg), 'en') for bg in bigrams]
        score += 0.15 * (sum(bigram_scores) / len(bigram_scores))

    return score


def choose_best_sentence(candidates):
    """Pick the most natural-sounding candidate using the fluency score.
    
    Returns a smoothed, lower-case sentence fragment (no capitalization),
    so callers can embed it and decide when to capitalize.
    """
    best = None
    best_score = float("-inf")
    for cand in candidates:
        if not cand:
            continue
        smoothed = smooth_grammar(cand)
        score = _ngram_fluency_score(smoothed)
        if score > best_score:
            best_score = score
            best = smoothed
    return best or ""


#### Precedence clarification patterns ####
# These patterns handle cases where operator precedence needs to be made explicit in English

# Pattern: (p & q) U r or (p | q) U r
# When And/Or is the left operand of Until, use natural phrasing without "the state that"
@pattern
def and_or_until_precedence_pattern(node):
    if type(node) is ltlnode.UntilNode:
        if type(node.left) in (ltlnode.AndNode, ltlnode.OrNode):
            left_eng = clean_for_composition(node.left.__to_english__())
            right_eng = clean_for_composition(node.right.__to_english__())
            # Change "holds" to "hold" for grammatical agreement with compound subjects
            return f"{left_eng} hold until {right_eng}"
    return None


# Pattern: p & (q U r) or p | (q U r)
# When Until is an operand of And/Or, clarify with "the case where"
@pattern  
def until_in_and_precedence_pattern(node):
    if type(node) is ltlnode.AndNode:
        # Until expressions are naturally clausal and don't need "the case where" wrapper
        # Only intervene if we have an Until operand to ensure consistency
        if type(node.left) is ltlnode.UntilNode or type(node.right) is ltlnode.UntilNode:
            left_eng = clean_for_composition(node.left.__to_english__())
            right_eng = clean_for_composition(node.right.__to_english__())
            return f"both {left_eng} and {right_eng}"
    return None


@pattern
def until_in_or_precedence_pattern(node):
    if type(node) is ltlnode.OrNode:
        # Until expressions are naturally clausal and don't need "the case where" wrapper
        # Only intervene if we have an Until operand to ensure consistency
        if type(node.left) is ltlnode.UntilNode or type(node.right) is ltlnode.UntilNode:
            left_eng = clean_for_composition(node.left.__to_english__())
            right_eng = clean_for_composition(node.right.__to_english__())
            return f"either {left_eng} or {right_eng}"
    return None


#### Globally special cases ####

# G p (single literal)
# English: p holds at all times / p always holds
# More natural phrasings for simple globally of a literal
@pattern
def globally_literal_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.LiteralNode:
            lit_eng = clean_for_composition(op.__to_english__())
            patterns = [
                f"{lit_eng} holds at all times",
                f"{lit_eng} always holds",
                f"{lit_eng} must always hold",
                f"at all times, {lit_eng} holds"
            ]
            return choose_best_sentence(patterns)
    return None


# G (p & q) - globally conjunction
# English: always maintain both p and q / both p and q hold at all times
@pattern
def globally_and_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            patterns = [
                f"always maintain both {left_eng} and {right_eng}",
                f"both {left_eng} and {right_eng} must always hold",
                f"at all times, both {left_eng} and {right_eng} hold"
            ]
            return choose_best_sentence(patterns)
    return None


# G (p | q) - globally disjunction
# English: always have either p or q / either p or q holds at all times
@pattern
def globally_or_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.OrNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            patterns = [
                f"always have either {left_eng} or {right_eng}",
                f"either {left_eng} or {right_eng} must always hold",
                f"at all times, either {left_eng} or {right_eng} holds"
            ]
            return choose_best_sentence(patterns)
    return None


# G G ... G p (idempotent globally - G G = G)
# English: Always p / At all times p
# Source: G is idempotent: G G p ≡ G p
@pattern
def idempotent_globally_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            # Unwrap all consecutive Globally operators
            innermost = op.operand
            while type(innermost) is ltlnode.GloballyNode:
                innermost = innermost.operand
            inner_eng = clean_for_composition(innermost.__to_english__())
            return f"at all times, {inner_eng}"
    return None


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
# Source: This is the "recurrence" or "infinitely often" pattern from Manna & Pnueli
@pattern
def recurrence_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            inner_op = op.operand
            # Skip if inner is AndNode - let more specific pattern handle it
            if type(inner_op) is ltlnode.AndNode:
                return None
            # Handle G F (p -> q) - "infinitely often, if p then q"
            if type(inner_op) is ltlnode.ImpliesNode:
                # Check for G F (p -> G q) - special case
                if type(inner_op.right) is ltlnode.GloballyNode:
                    left_eng = clean_for_composition(inner_op.left.__to_english__())
                    right_eng = clean_for_composition(inner_op.right.operand.__to_english__())
                    return f"infinitely often, {left_eng} will trigger {right_eng} to hold permanently"
                left_eng = clean_for_composition(inner_op.left.__to_english__())
                right_eng = clean_for_composition(inner_op.right.__to_english__())
                return f"infinitely often, if {left_eng} then {right_eng}"
            # Handle G F G ... patterns (recurrence with nested globally)
            # G F G x = G F x by absorption (once you're in G F, adding more G F doesn't change meaning)
            # Source: Manna & Pnueli - alternating temporal operators
            if type(inner_op) is ltlnode.GloballyNode:
                # Unwrap to find innermost non-G-F alternation
                innermost = inner_op.operand
                while type(innermost) is ltlnode.FinallyNode or type(innermost) is ltlnode.GloballyNode:
                    innermost = innermost.operand
                inner_eng = clean_for_composition(innermost.__to_english__())
                return f"{inner_eng} will happen infinitely often"
            # Handle G F F x = G F x (F F = F)
            if type(inner_op) is ltlnode.FinallyNode:
                innermost = inner_op.operand
                while type(innermost) is ltlnode.FinallyNode:
                    innermost = innermost.operand
                inner_eng = clean_for_composition(innermost.__to_english__())
                return f"{inner_eng} will happen infinitely often"
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
                    return choose_best_sentence([
                        f"once {left_eng} is true, it stays true",
                        f"once {left_eng} becomes true, it remains true",
                        f"after {left_eng} holds, it continues to hold forever"
                    ])
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


## Immediate Response Pattern
# Pattern: G(p -> X q)
# English: Whenever p (holds), q must hold in the very next step
# Source: Dwyer, M.B., Avrunin, G.S., Corbett, J.C. "Patterns in Property Specifications for Finite-State Verification"
#         Proceedings of ICSE 1999. http://patterns.projects.cs.ksu.edu/
@pattern
def immediate_response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.NextNode:
                # Don't match if it's the final state pattern G(p -> X p)
                if (type(left) is ltlnode.LiteralNode and 
                    type(right.operand) is ltlnode.LiteralNode and
                    left.value == right.operand.value):
                    return None
                left_eng = clean_for_composition(left.__to_english__())
                right_eng = clean_for_composition(right.operand.__to_english__())
                return f"whenever {left_eng}, {right_eng} must hold in the next step"
    return None


## Bounded Response Pattern  
# Pattern: G(p -> X(F q))
# English: Whenever p (holds), q will eventually occur (starting from the next step)
# Source: Dwyer et al. "Patterns in Property Specifications" ICSE 1999
#         This is a variant of the response pattern with a one-step delay
@pattern
def bounded_response_pattern_to_english(node):
    if type(node) is ltlnode.GloballyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.NextNode:
                inner = right.operand
                if type(inner) is ltlnode.FinallyNode:
                    left_eng = clean_for_composition(left.__to_english__())
                    right_eng = clean_for_composition(inner.operand.__to_english__())
                    return f"whenever {left_eng}, {right_eng} will eventually occur after the next step"
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
            # For literals, use simpler phrasing with multiple alternatives
            if type(negated) is ltlnode.LiteralNode:
                patterns = [
                    f"{negated_eng} will never occur",
                    f"always avoid {negated_eng}",
                    f"never {negated_eng}",
                    f"{negated_eng} must never happen"
                ]
                return choose_best_sentence(patterns)
            return f"it is never the case that {negated_eng}"


#### Finally special cases ####

# F F ... F p (idempotent finally - F F = F)
# English: Eventually p
# Source: F is idempotent: F F p ≡ F p
@pattern
def idempotent_finally_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.FinallyNode:
            # Unwrap all consecutive Finally operators
            innermost = op.operand
            while type(innermost) is ltlnode.FinallyNode:
                innermost = innermost.operand
            inner_eng = clean_for_composition(innermost.__to_english__())
            return f"eventually, {inner_eng}"
    return None


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
            # Skip if inner is AndNode - let persistence pattern handle it
            if type(inner) is ltlnode.AndNode:
                return None
            # Handle F G (p -> q) - "eventually, the rule 'if p then q' will always hold"
            if type(inner) is ltlnode.ImpliesNode:
                left_eng = clean_for_composition(inner.left.__to_english__())
                right_eng = clean_for_composition(inner.right.__to_english__())
                return f"eventually, the rule 'if {left_eng} then {right_eng}' will always hold"
            # Handle F G F ... patterns (eventual recurrence) - collapses to G F by absorption
            # Source: Manna & Pnueli - alternating F/G chains simplify
            if type(inner) is ltlnode.FinallyNode:
                # F G F x = "eventually, x will happen infinitely often"
                # Keep unwinding to find the innermost
                innermost = inner.operand
                while type(innermost) is ltlnode.GloballyNode or type(innermost) is ltlnode.FinallyNode:
                    innermost = innermost.operand
                inner_eng = clean_for_composition(innermost.__to_english__())
                return f"eventually, {inner_eng} will happen infinitely often"
            # Handle F G G x = F G x (G G = G)
            if type(inner) is ltlnode.GloballyNode:
                innermost = inner.operand
                while type(innermost) is ltlnode.GloballyNode:
                    innermost = innermost.operand
                inner_eng = clean_for_composition(innermost.__to_english__())
                return f"eventually, {inner_eng} will become true and remain true forever"
            inner_eng = clean_for_composition(inner.__to_english__())
            return f"eventually, {inner_eng} will always be true"
    return None


## Persistence Pattern (Stability)
# Pattern: F(G p)
# English: Eventually p will become true and remain true forever
# Source: Manna, Z. and Pnueli, A. "The Temporal Logic of Reactive and Concurrent Systems" (1992)
#         Also known as "stability" - the system eventually stabilizes to a state where p holds
# Note: This is the same structure as finally_globally but with literal-specific phrasing
@pattern
def persistence_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.GloballyNode:
            inner = op.operand
            # Only match simple literals for this specific phrasing
            if type(inner) is ltlnode.LiteralNode:
                inner_eng = clean_for_composition(inner.__to_english__())
                return f"eventually {inner_eng} will become true and stay true forever"
    return None


## Persistence After Trigger Pattern
# Pattern: F(p & G q)
# English: Eventually p will occur and from that point on, q will always hold
# Source: Dwyer et al. "Patterns in Property Specifications" ICSE 1999
#         This captures scenarios where a trigger event causes a permanent change
@pattern
def persistence_after_trigger_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            left = op.left
            right = op.right
            # Check for p & G q
            if type(right) is ltlnode.GloballyNode:
                trigger_eng = clean_for_composition(left.__to_english__())
                persistent_eng = clean_for_composition(right.operand.__to_english__())
                return f"eventually {trigger_eng} will occur, and from then on {persistent_eng} will always hold"
            # Check for G p & q (reversed order)
            if type(left) is ltlnode.GloballyNode:
                trigger_eng = clean_for_composition(right.__to_english__())
                persistent_eng = clean_for_composition(left.operand.__to_english__())
                return f"eventually {trigger_eng} will occur, and from then on {persistent_eng} will always hold"
    return None


## Trigger-to-Permanence Pattern
# Pattern: F(p -> G q)
# English: Eventually, once p occurs, q will hold forever after
# Source: Common requirements pattern - "eventually a trigger causes permanent behavior"
@pattern
def trigger_to_permanence_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left = op.left
            right = op.right
            if type(right) is ltlnode.GloballyNode:
                trigger_eng = clean_for_composition(left.__to_english__())
                result_eng = clean_for_composition(right.operand.__to_english__())
                return f"eventually, once {trigger_eng}, then {result_eng} will hold forever after"
    return None


# F (p & q)
# English: Eventually at the same time, p and q will (hold)
@pattern
def finally_and_pattern_to_english(node):
    if type(node) is ltlnode.FinallyNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            # Skip if one side is GloballyNode - let persistence_after_trigger handle it
            if type(op.left) is ltlnode.GloballyNode or type(op.right) is ltlnode.GloballyNode:
                return None
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
            patterns = [
                f"{inner_eng} will never occur",
                f"never {inner_eng}",
                f"{inner_eng} is impossible"
            ]
            return choose_best_sentence(patterns)
    return None


# !G( !( p & X p ) ) - Recovery pattern with grace period
# This means: it's not always the case that !(p & X p), which means
# eventually p & X p will happen, indicating p holds in consecutive steps
@pattern  
def recovery_pattern_to_english(node):
    """Detect and translate the recovery pattern !G(!(p & X p))."""
    # Early return if not a NotNode
    if type(node) is not ltlnode.NotNode:
        return None
    
    op = node.operand
    if type(op) is not ltlnode.GloballyNode:
        return None
    
    inner = op.operand
    if type(inner) is not ltlnode.NotNode:
        return None
    
    innermost = inner.operand
    if type(innermost) is not ltlnode.AndNode:
        return None
    
    # Check for pattern p & X p where both p's are the same literal
    left = innermost.left
    right = innermost.right
    
    if type(right) is not ltlnode.NextNode:
        return None
    
    if not (type(left) is ltlnode.LiteralNode and 
            type(right.operand) is ltlnode.LiteralNode and
            left.value == right.operand.value):
        return None
    
    # Pattern matched! Provide alternative phrasings
    lit_eng = clean_for_composition(left.__to_english__())
    patterns = [
        f"{lit_eng} should eventually hold in consecutive steps, with a grace period for recovery",
        f"{lit_eng} must eventually occur in back-to-back steps, allowing for recovery",
        f"{lit_eng} will eventually happen consecutively, with recovery allowed"
    ]
    return choose_best_sentence(patterns)


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


# Pattern: (p U q) | G p  -- weak until phrasing
@pattern
def weak_until_disjunction_pattern_to_english(node):
    if type(node) is ltlnode.OrNode:
        left, right = node.left, node.right

        def match(until, glob):
            if type(until) is ltlnode.UntilNode and type(glob) is ltlnode.GloballyNode:
                p, q = until.left, until.right
                if ltlnode.LTLNode.equiv(str(p), str(glob.operand)):
                    p_eng = clean_for_composition(p.__to_english__())
                    q_eng = clean_for_composition(q.__to_english__())
                    return choose_best_sentence([
                        # Canonical: explicit case split
                        f"{p_eng} holds until {q_eng} happens, or {p_eng} holds forever if {q_eng} never happens",
                        # Template B: conditional termination
                        f"{p_eng} keeps holding and stops only if {q_eng} happens",
                    ])
            return None

        # Handle (p U q) ∨ G p and G p ∨ (p U q)
        return match(left, right) or match(right, left)

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


@pattern
def aligned_next_implication_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        left_steps, left_core = _count_next_chain(node.left)
        right_steps, right_core = _count_next_chain(node.right)

        if left_steps >= 1 and right_steps >= left_steps and right_steps > 0:
            left_eng = clean_for_composition(left_core.__to_english__())
            right_eng = clean_for_composition(right_core.__to_english__())

            gap = right_steps - left_steps
            if left_steps == 1:
                left_clause = "in the next step"
            else:
                left_clause = f"in {_steps_phrase(left_steps)}"

            if gap == 0:
                timing = "in that same step"
            elif gap == 1:
                timing = "in the following step"
            else:
                timing = f"{_steps_phrase(gap)} after that"

            absolute = f"in {_steps_phrase(right_steps)} from now"
            return f"if {left_clause}, {left_eng}, then {timing} ({absolute}), {right_eng}"
    return None


@pattern
def aligned_next_boolean_pattern_to_english(node):
    if type(node) in (ltlnode.AndNode, ltlnode.OrNode):
        left_steps, left_core = _count_next_chain(node.left)
        right_steps, right_core = _count_next_chain(node.right)

        if left_steps >= 1 and right_steps == left_steps:
            shared_clause = "in the next step" if left_steps == 1 else f"in {_steps_phrase(left_steps)}"
            left_eng = clean_for_composition(left_core.__to_english__())
            right_eng = clean_for_composition(right_core.__to_english__())

            if type(node) is ltlnode.AndNode:
                return f"{shared_clause}, both {left_eng} and {right_eng}"
            return f"{shared_clause}, either {left_eng} or {right_eng}"
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


#### Propositional Logic Patterns ####
# These patterns handle common propositional logic structures that can be awkward in English
# Source: Standard logical equivalences and De Morgan's laws

# Pattern: !!p (double negation)
# English: p (simplified)
@pattern
def double_negation_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.NotNode:
            inner_eng = op.operand.__to_english__()
            return inner_eng  # Already capitalized from inner call
    return None


# Pattern: !(p & q) (negated conjunction - De Morgan)
# English: not both p and q / either not p or not q
# Source: De Morgan's Laws - more natural to say "not both" than "it is not the case that both"
@pattern
def negated_and_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.AndNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            return f"not both {left_eng} and {right_eng}"
    return None


# Pattern: !(p | q) (negated disjunction - De Morgan)  
# English: neither p nor q
# Source: De Morgan's Laws - "neither...nor" is the natural English form
@pattern
def negated_or_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.OrNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            return f"neither {left_eng} nor {right_eng}"
    return None


# Pattern: !(p -> q) (negated implication)
# English: p but not q
# Logically equivalent to: p & !q
# Source: Material implication - negating "if p then q" means p is true but q is false
@pattern
def negated_implication_pattern_to_english(node):
    if type(node) is ltlnode.NotNode:
        op = node.operand
        if type(op) is ltlnode.ImpliesNode:
            left_eng = clean_for_composition(op.left.__to_english__())
            right_eng = clean_for_composition(op.right.__to_english__())
            return f"{left_eng}, but not {right_eng}"
    return None


# Pattern: p -> !q
# English: if p, then not q / p excludes q
@pattern
def implies_negation_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        right = node.right
        if type(right) is ltlnode.NotNode:
            left_eng = clean_for_composition(node.left.__to_english__())
            right_eng = clean_for_composition(right.operand.__to_english__())
            # For simple literals, use cleaner phrasing
            if type(node.left) is ltlnode.LiteralNode and type(right.operand) is ltlnode.LiteralNode:
                return f"{left_eng} excludes {right_eng}"
            return f"if {left_eng}, then not {right_eng}"
    return None


# Pattern: !p -> q  
# English: if not p, then q / q unless p
@pattern
def negation_implies_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        left = node.left
        if type(left) is ltlnode.NotNode:
            left_eng = clean_for_composition(left.operand.__to_english__())
            right_eng = clean_for_composition(node.right.__to_english__())
            return f"{right_eng} unless {left_eng}"
    return None


# Pattern: !p & !q
# English: neither p nor q (same as !(p | q) by De Morgan)
@pattern
def and_of_negations_pattern_to_english(node):
    if type(node) is ltlnode.AndNode:
        left = node.left
        right = node.right
        if type(left) is ltlnode.NotNode and type(right) is ltlnode.NotNode:
            left_eng = clean_for_composition(left.operand.__to_english__())
            right_eng = clean_for_composition(right.operand.__to_english__())
            return f"neither {left_eng} nor {right_eng}"
    return None


# Pattern: !p | !q
# English: not both p and q (same as !(p & q) by De Morgan)
@pattern
def or_of_negations_pattern_to_english(node):
    if type(node) is ltlnode.OrNode:
        left = node.left
        right = node.right
        if type(left) is ltlnode.NotNode and type(right) is ltlnode.NotNode:
            left_eng = clean_for_composition(left.operand.__to_english__())
            right_eng = clean_for_composition(right.operand.__to_english__())
            return f"not both {left_eng} and {right_eng}"
    return None


# Pattern: (p & q) -> r
# English: if both p and q, then r
@pattern
def conjunction_implies_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        left = node.left
        if type(left) is ltlnode.AndNode:
            p_eng = clean_for_composition(left.left.__to_english__())
            q_eng = clean_for_composition(left.right.__to_english__())
            r_eng = clean_for_composition(node.right.__to_english__())
            return f"if both {p_eng} and {q_eng}, then {r_eng}"
    return None


# Pattern: (p | q) -> r
# English: if either p or q, then r
@pattern
def disjunction_implies_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        left = node.left
        if type(left) is ltlnode.OrNode:
            p_eng = clean_for_composition(left.left.__to_english__())
            q_eng = clean_for_composition(left.right.__to_english__())
            r_eng = clean_for_composition(node.right.__to_english__())
            return f"if either {p_eng} or {q_eng}, then {r_eng}"
    return None


# Pattern: p -> (q & r)
# English: if p, then both q and r
@pattern
def implies_conjunction_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        right = node.right
        if type(right) is ltlnode.AndNode:
            # Skip if this looks like a temporal pattern (F inside)
            if type(right.left) is ltlnode.FinallyNode or type(right.right) is ltlnode.FinallyNode:
                return None
            p_eng = clean_for_composition(node.left.__to_english__())
            q_eng = clean_for_composition(right.left.__to_english__())
            r_eng = clean_for_composition(right.right.__to_english__())
            return f"if {p_eng}, then both {q_eng} and {r_eng}"
    return None


# Pattern: p -> (q | r)
# English: if p, then either q or r
@pattern
def implies_disjunction_pattern_to_english(node):
    if type(node) is ltlnode.ImpliesNode:
        right = node.right
        if type(right) is ltlnode.OrNode:
            p_eng = clean_for_composition(node.left.__to_english__())
            q_eng = clean_for_composition(right.left.__to_english__())
            r_eng = clean_for_composition(right.right.__to_english__())
            return f"if {p_eng}, then either {q_eng} or {r_eng}"
    return None


def apply_special_pattern_if_possible(node):

    for pattern in patterns:
        result = pattern(node)
        if result is not None:
            # Apply grammar smoothing but NOT capitalization (defer to finalize_sentence)
            result = smooth_grammar(result)
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
