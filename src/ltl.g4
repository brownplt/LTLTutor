grammar ltl;

ltl: formula EOF;

formula
    : formula '|' formula                     # disjunction
    | formula '&' formula                     # conjunction
    | formula ( 'U' | 'UNTIL' ) formula       # U
    | formula '->' formula                    # implication
    | formula '<->' formula                   # equivalence
    | ('X' | 'AFTER' | 'NEXT_STATE') formula   # X
    | ('F' | 'EVENTUALLY') formula            # F
    | ('G' | 'ALWAYS') formula                # G
    | '!' formula                             # not
    | '(' formula ')'                         # parentheses
    | atomicFormula                           # literal
    ;

atomicFormula: ID;

ID : [a-z0-9]+ ;

// Skip whitespace
WS : [ \t\r\n]+ -> skip ;