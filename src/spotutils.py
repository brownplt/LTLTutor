import spot



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

## This is wrong ##
def generate_accepting_words(automaton, max_runs=5):
    words = []
    for _ in range(max_runs):
        run = automaton.accepting_run()
        if run:
            # Convert run to a word that the automaton accepts
            prefix_word = [step.label for step in run.prefix]
            cycle_word = [step.label for step in run.cycle] if run.cycle else []
            words.append((prefix_word, cycle_word))
        else:
            break  # Stop if no further accepting run is found
    return words

def generate_traces(formula, max_traces=5):
    # Parse the LTL formula
    f = spot.formula(formula)
    
    # Translate the LTL formula to a Büchi automaton
    automaton = f.translate()
    
    # Retrieve and return the acceptance condition
    runs = generate_accepting_words(automaton, max_traces)
    return runs



