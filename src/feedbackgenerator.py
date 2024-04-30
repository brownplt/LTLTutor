import spotutils


def getRelationship(formula1, formula2):
    """
    Returns the relationship between two formulas.
    :param formula1: The first formula.
    :param formula2: The second formula.
    :return: The relationship between the two formulas.
    """

    
    f1_subsumes_f2 = spotutils.isNecessaryFor(formula1, formula2)
    f2_subsumes_f1 = spotutils.isNecessaryFor(formula2, formula1)
    disjoint = spotutils.areDisjoint(formula1, formula2)

    return {
        'subsumed': f1_subsumes_f2,
        'contained': f2_subsumes_f1,
        'disjoint': disjoint
    }