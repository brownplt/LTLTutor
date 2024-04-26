
## Generating Parser from ANTLR
```
antlr4 -Dlanguage=Python3 ltl.g4
```

## Running tests



## Running Server


# TODO:



### Inner Loop
- Distractor generator (Given solution, generate common misconception based distractors)
- Checker of equivalency, etc.
- Misconception Identifier (Given solution, expected solution : Check equiv, if not equiv determine issue) --- can we do this by examining the unsat core of f1 iff f2
- LTLf to English?
- SMT w/ LTLf?



### Outer Loop

- Build student model (which misconceptions do they exhibit?)
- Determine Interleaving behavior
- Determine distribution of questions, choose distractor from questions.