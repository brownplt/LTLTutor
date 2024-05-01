import spot



DEFAULT_LTL_PRIORITIES = {
    "ap" : 3,
    "false": 1,
    "true":1,
    "not":1,
    "F":1,
    "G":1,
    "X":1,
    "Closure":0, ## ?
    "equiv":1,
    "implies":1,
    "xor":0,
    "R":0,
    "U":1,
    "W":0,
    "M":0,
    "and":1,
    "or":1,
    "EConcat":0,
    "UConcat":0
}


def areEquivalent(formula1, formula2):
    
    # Parse the formulas
    f1 = spot.formula(str(formula1))
    f2 = spot.formula(str(formula2))

    # Check if they are equivalent
    return spot.formula.are_equivalent(f1, f2)

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
    words = []
    for _ in range(max_runs):
        run = automaton.accepting_run()
        if run:
            # Convert run to a word that the automaton accepts
            word = spot.twa_word(run)
            word = str(word)
            words.append(word)
        else:
            break  # Stop if no further accepting run is found
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

def gen_rand_ltl(atoms, tree_size, ltl_priorities, num_formulae = 5):
    
    def to_priority_string(d):
        return ','.join(f'{k}={v}' for k, v in d.items())

    # Need to do the correct kind of manipulation here
    ltl_priorities_string = to_priority_string(ltl_priorities)

    f = spot.randltl(atoms, tree_size=tree_size, ltl_priorities = ltl_priorities)
    
    ### TODO: Need to change from SPOT output to our output
    #Ex. spot      p1 U (p2 R (p3 & !p4))
    # I think spot uses | for or

    return [str(next(f)) for _ in range(num_formulae)]