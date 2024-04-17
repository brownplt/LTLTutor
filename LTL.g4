grammar LTL;

ltl: formula EOF;

formula: atomicFormula
    | '(' formula ')'
    | formula '=>' formula
    | formula '<=>' formula
    | formula 'U' formula
    | 'X' formula
    | 'F' formula
    | 'G' formula
    | formula '&&' formula
    | formula '||' formula
    | '!' formula;

atomicFormula: ID;

ID: [a-zA-Z]+;