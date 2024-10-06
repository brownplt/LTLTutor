grammar ltl;

ltl: formula EOF;

formula
    : formula '|' formula       # disjunction
    | formula '&' formula       # conjunction
    | formula ( 'U' | 'UNTIL' ) formula       # until
    | formula '->' formula      # implication
    | formula '<->' formula     # equivalence
    | ('X' | 'NEXT' | 'NEXT_STATE') formula    # next
    | ('F' | 'EVENTUALLY') formula  # eventually
    | ('G' | 'ALWAYS') formula  # always
    | '!' formula              # not
    | '(' formula ')'          # parentheses
    | atomicFormula            # literal
    ;

atomicFormula: ID;

ID : [a-z0-9]+ ;

// Skip whitespace
WS : [ \t\r\n]+ -> skip ;