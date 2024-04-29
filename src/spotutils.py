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



def generate_accepting_runs(automaton, max_runs=5):
    runs = []
    for _ in range(max_runs):
        run = automaton.accepting_run()
        if run:
            # Convert run to a readable format, typically involving state and transition labels
            trace = [(state.cond_str(), list(transition)) for state, transition in run]
            runs.append(trace)
        else:
            break  # Stop if no further accepting run is found
    return runs

def generate_traces(formula, max_traces=5):
    # Parse the LTL formula
    f = spot.formula(formula)
    
    # Translate the LTL formula to a Büchi automaton
    automaton = f.translate()
    
    # Retrieve and return the acceptance condition
    runs = generate_accepting_runs(automaton, max_traces)
    return runs



