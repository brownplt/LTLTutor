import spot


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




def generate_acceptance_condition(formula):
    # Parse the LTL formula
    f = spot.formula(formula)
    
    # Translate the LTL formula to a Büchi automaton
    automaton = f.translate()
    
    # Retrieve and return the acceptance condition
    acceptance_condition = automaton.get_acceptance()
    return acceptance_condition



