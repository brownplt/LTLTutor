grammar ltl;

ltl: formula EOF;

formula
    : '!' formula                             # not
    | ('X' | 'AFTER' | 'NEXT_STATE') formula   # X
    | ('F' | 'EVENTUALLY') formula            # F
    | ('G' | 'ALWAYS') formula                # G
    | formula '&' formula                       # conjunction
    | formula '|' formula                       # disjunction
    | formula ( 'U' | 'UNTIL' ) formula         # U
    | formula '->' formula                      # implication
    | formula '<->' formula                     # equivalence
    | '(' formula ')'                           # parentheses
    | atomicFormula                             # literal
    ;

atomicFormula: ID;

ID : [a-z0-9]+ ;

// Skip whitespace
WS : [ \t\r\n]+ -> skip ;