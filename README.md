
## Generating Parser from ANTLR
```
npx antlr4ts LTL.g4           
```

## Running tests

```
cd test
npx jest filename.test.ts
```


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