grammar ltl;

ltl: formula EOF;

formula
    : formula '|' formula     # disjunction
    | formula '&' formula     # conjunction
    | formula 'U' formula      # until
    | formula '->' formula     # implication
    | formula '<->' formula    # equivalence
    | 'X' formula             # X
    | 'F' formula              # F
    | 'G' formula            # G
    | '!' formula              # not
    | '(' formula ')'          # parentheses
    | atomicFormula            # literal
    ;

atomicFormula: ID;

ID : [a-z0-9]+ ;