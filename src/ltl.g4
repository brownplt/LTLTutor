grammar ltl;

ltl: formula EOF;

X : 'X' ;
F : 'F' ;
G : 'G' ;
NOT : '!' ;
OR : '|' ;
AND : '&' ;
U : 'U' ;
IMPLIES : '->' ;
EQUIV : '<->' ;
ID : [A-EH-TVWYZa-z0-9]+ ;

formula
    : formula OR formula     # disjunction
    | formula AND formula     # conjunction
    | formula U formula      # until
    | formula IMPLIES formula     # implication
    | formula EQUIV formula    # equivalence
    | X formula             # X
    | F formula              # F
    | G formula            # G
    | NOT formula              # not
    | '(' formula ')'          # parentheses
    | ID                      # literal
    ;