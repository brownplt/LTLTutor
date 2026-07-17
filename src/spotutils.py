import spot
import random


DEFAULT_WEIGHT = 5
DEFAULT_WEIGHT_TEMPORAL = 7
DEFAULT_LTL_PRIORITIES = {
    "ap" : DEFAULT_WEIGHT, 

    "F": DEFAULT_WEIGHT_TEMPORAL,
    "G": DEFAULT_WEIGHT_TEMPORAL,
    "X": DEFAULT_WEIGHT_TEMPORAL,

    "U": DEFAULT_WEIGHT_TEMPORAL,
    "and": DEFAULT_WEIGHT,
    "or": DEFAULT_WEIGHT,
    "equiv": DEFAULT_WEIGHT,
    "implies":DEFAULT_WEIGHT,
    "not": DEFAULT_WEIGHT,
    ## TODO: Examine: Perhaps not so many trues and falses?
    "false": 1,
    "true":1,
    "W":0,
    "M":0,
    "xor":0,
    "R":0,

    ## Aren't these PSL not LTL
    # "EConcat":0,
    # "UConcat":0,
    # "Closure":0, ## ?
}


def _count_trace_steps(trace):
    """
    Count the number of steps in a trace string.
    Traces use ';' as a step delimiter (e.g., 'a; b; cycle{c}' has 3 steps).
    """
    return len(trace.split(';'))


def weighted_trace_choice(traces):
    """
    Select a trace from a list of traces, with shorter traces slightly preferred.
    Uses inverse step count weighting: weight = 1 / (1 + num_steps).
    This gives shorter traces higher selection probability while still allowing
    longer traces to be selected.
    
    Args:
        traces: A list of trace strings to choose from
        
    Returns:
        A randomly selected trace string, with shorter traces more likely to be chosen
    """
    if not traces:
        raise ValueError("Cannot choose from empty list of traces")
    if len(traces) == 1:
        return traces[0]
    
    # Calculate weights based on inverse step count
    # Using 1 / (1 + num_steps) to slightly prefer shorter traces
    weights = [1.0 / (1.0 + _count_trace_steps(t)) for t in traces]
    
    return random.choices(traces, weights=weights, k=1)[0]


def areEquivalent(formula1, formula2):
    return isSufficientFor(formula1, formula2) and isNecessaryFor(formula1, formula2)



'''
Returns true if f => g is a tautology
'''
def isSufficientFor(f, g):

    f = spot.parse_formula(str(f))
    g = spot.parse_formula(str(g))


    a_f = f.translate()
    a_ng = spot.formula.Not(g).translate()
    return spot.product(a_f, a_ng).is_empty()


'''
Returns true if g => f is a tautology
'''
def isNecessaryFor(f, g):
    return isSufficientFor(g, f)


def areDisjoint(f, g):
    ff = spot.parse_formula(str(f))
    gf = spot.parse_formula(str(g))

    a_ff = ff.translate()
    a_gf = gf.translate()

    return spot.product(a_ff, a_gf).is_empty()


def generate_accepting_words(automaton, max_runs=5):
    """Generate up to max_runs distinct accepting words by excluding previously seen traces."""
    words = []
    current_aut = automaton
    
    for _ in range(max_runs):
        # Check if current automaton is empty
        if current_aut.is_empty():
            break
            
        run = current_aut.accepting_run()
        if run:
            # Convert run to a word that the automaton accepts
            word = spot.twa_word(run)
            word_str = str(word)
            
            # Only add if we haven't seen it (safety check)
            if word_str not in words:
                words.append(word_str)
            
            # Exclude this trace from future runs
            try:
                # Build automaton that accepts only this trace
                trace_aut = word.as_automaton()
                # Complement it (now accepts everything EXCEPT this trace)
                not_trace_aut = spot.complement(trace_aut)
                # Product with current automaton to exclude this trace
                current_aut = spot.product(current_aut, not_trace_aut)
            except Exception as e:
                print(f"Warning: Could not exclude trace '{word_str}': {e}")
                break
        else:
            break  # Stop if no accepting run is found
    return words

def generate_accepted_traces(formula, max_traces=5):
    # Parse the LTL formula
    f = spot.formula(formula)
    
    # Translate the LTL formula to a Büchi automaton
    automaton = f.translate()
    
    # Retrieve and return the acceptance condition
    runs = generate_accepting_words(automaton, max_traces)
    #w.as_automaton() shows the run as an automaton.
    return runs

## Generate traces accepted by f_accepted, and rejected by f_rejected
def generate_traces(f_accepted, f_rejected, max_traces=5):
    # Parse the LTL formula
    f_a = spot.formula(f_accepted)
    f_r = spot.formula.Not(spot.formula(f_rejected))

    f = spot.formula.And([f_a, f_r])
    automaton = f.translate()
    runs = generate_accepting_words(automaton, max_traces)
    #w.as_automaton() shows the run as an automaton.
    return runs



# https://spot-sandbox.lrde.epita.fr/notebooks/examples%20(read%20only)/randltl.ipynb

## TODO: Need to generate some sort of transform from Misconceptions to ltl_priorities
## That is -- each misconception should have some weight around related concepts
### Some are obvious : Implicit G means, add more G
### Some are less obvious: eg "BadStateIndex"

# Operators outside the tutor's grammar (ltl.g4).  randltl never emits them
# (their priorities are zeroed), but SPOT's simplifier can introduce them,
# e.g. !(a U b) -> !a R !b.
_NON_GRAMMAR_OPS = (spot.op_W, spot.op_M, spot.op_R, spot.op_Xor)


def _in_tutor_grammar(f):
    if f.kind() in _NON_GRAMMAR_OPS:
        return False
    return all(_in_tutor_grammar(child) for child in f)


def _rewrite_to_tutor_grammar(f):
    """Rewrite W/M/R/xor into the tutor's operator set via exact identities.

    These direct identities duplicate at most one operand once; SPOT's own
    unabbreviate() instead chains R -> W -> U and can triple subterms.
    Since R only ever arises here from the simplifier normalizing a negated
    until, !a R !b maps straight back to !(a U b) (the formula constructors
    cancel the double negations).
    """
    f = f.map(_rewrite_to_tutor_grammar)
    kind = f.kind()
    if kind == spot.op_R:
        # a R b == !(!a U !b)
        return spot.formula.Not(spot.formula.U(
            spot.formula.Not(f[0]), spot.formula.Not(f[1])))
    if kind == spot.op_W:
        # a W b == (a U b) | G a
        return spot.formula.Or([spot.formula.U(f[0], f[1]),
                                spot.formula.G(f[0])])
    if kind == spot.op_M:
        # a M b == b U (a & b)
        return spot.formula.U(f[1], spot.formula.And([f[0], f[1]]))
    if kind == spot.op_Xor:
        # a xor b == !(a <-> b)
        return spot.formula.Not(spot.formula.Equiv(f[0], f[1]))
    return f


def gen_rand_ltl(atoms, tree_size, ltl_priorities, num_formulae = 5):

    def to_priority_string(d):
        # SPOT's priority parser tokenizes the string buffer in place,
        # corrupting the Python string it was handed; always build a fresh
        # string here rather than reusing a shared constant.
        return ','.join(f'{k}={v}' for k, v in d.items())

    def new_generator():
        # simplify=3 (randltl's own default level) rewrites away redundant
        # nestings like F G F G d that read absurdly when rendered as English.
        # randltl's default seed is 0, and we build a fresh generator per
        # call, so without an explicit seed every call would yield the same
        # sequence.  The priority string is rebuilt each time (see above).
        return spot.randltl(atoms, tree_size=tree_size,
                            ltl_priorities=to_priority_string(ltl_priorities),
                            simplify=3, seed=random.randrange(2**30))

    # Simplification can collapse a formula to a constant (skip those and
    # keep drawing) or rewrite it into W/M/R/xor, which the tutor cannot
    # parse or display (rewrite those back into the tutor's operator set).
    # Keep drawing until the requested batch is filled; a generator only
    # yields distinct formulas, so when it exhausts the unique-formula space
    # at this tree size, reseed a fresh one (duplicates across generators
    # are acceptable — callers ask for a pool, not a set).  The draw budget
    # is a safety net against pathologically tiny formula spaces.
    f = new_generator()
    formulae = []
    for _ in range(max(num_formulae * 50, 500)):
        if len(formulae) >= num_formulae:
            break
        try:
            candidate = next(f)
        except StopIteration:
            candidate = None
        if candidate is None:
            f = new_generator()
            continue
        if candidate.is_tt() or candidate.is_ff():
            continue
        candidate = _rewrite_to_tutor_grammar(candidate)
        if not _in_tutor_grammar(candidate):
            continue
        formulae.append(str(candidate))
    return formulae


def is_trivial(formula_str):
    """
    Check if a formula is a tautology or contradiction using SPOT.
    
    Args:
        formula_str: String representation of an LTL formula
        
    Returns:
        True if the formula simplifies to constant true (1) or false (0)
    """
    try:
        f = spot.formula(formula_str)
        # Simplify and check if it's constant true (1) or false (0)
        simplified = spot.simplify(f)
        simplified_str = str(simplified)
        return simplified_str in ['1', '0', 'true', 'false']
    except:
        return False


def gen_small_rand_ltl(atoms, tree_size=3, max_attempts=10):
    """
    Generate a single small non-trivial random LTL formula using SPOT.
    Prioritizes atomic propositions and simple operators to avoid complexity.
    
    Args:
        atoms: List of atomic proposition strings
        tree_size: Maximum tree size for the formula (default 3)
        max_attempts: Maximum number of attempts to find a non-trivial formula
        
    Returns:
        String representation of a non-trivial LTL formula, or a random atom as fallback
    """
    # Prioritize simple operators, keep tree size small
    priorities = {
        'ap': 5,
        'G': 2, 'F': 2, 'X': 2, 'U': 3,
        'and': 4, 'or': 4, 'implies': 3, 'not': 3,
        'equiv': 1, 'xor': 0, 'R': 0, 'W': 0, 'M': 0,
        'true': 0, 'false': 0
    }
    
    for _ in range(max_attempts):
        try:
            formulas = gen_rand_ltl(atoms, tree_size, priorities, num_formulae=1)
            formula_str = formulas[0]
            
            # Reject trivial formulas
            if not is_trivial(formula_str):
                return formula_str
        except:
            continue
    
    # Fallback to a simple literal if all attempts fail
    return random.choice(atoms)


## Returns the Mana Pneulli classification of the formula
def get_mana_pneulli_class(formula):



    f = spot.formula(formula)
    return spot.mp_class(f, 'v')


def get_aut_size(formula):
    f = spot.formula(formula)
    aut = spot.translate(f)
    num_states = aut.num_states()
    return num_states


### Given an LTL Trace, return if the formula is satisfied

### This works on the spot kernel but not here. Why?
def is_trace_satisfied(trace, formula):
    formula = str(formula)
    trace = str(trace)

    # Parse the trace into a word
    word = spot.parse_word(trace)

    # Words can be translated to automata
    # w.as_automaton()

    # Translate the formula into an automaton
    f = spot.formula(formula)
    aut = f.translate()
    wordaut = word.as_automaton()

    # Check if the automaton intersects with the word automaton
    return aut.intersects(wordaut)