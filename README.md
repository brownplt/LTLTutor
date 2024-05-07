
## Generating Parser from ANTLR
```
antlr4 -Dlanguage=Python3 ltl.g4
```

## Running tests



## Running Server


# TODO:


[x] SPOT is not supported on M1 macs or Windows. Need to think of an alternative here. https://spot.lre.epita.fr/install.html


### Inner Loop
- [] Question generation
    - [x] Distractor generator (Given solution, generate common misconception based distractors)
    - [] Generate answer from Natural Language (Maybe using `nl2ltl`)


- [] LTL -> Natural Language


- Misconception Identifier (Given solution, expected solution : Check equiv, if not equiv determine issue) --- can we do this by examining (answer) iff (incorrect)
- [] LTL to English?- How can we determine 


- [] LTL trace -> visualization. This helps generate satisfying and *not* satisfying trace examples.
  - [] Can do this to change the kind of question (From Formula selection -> trace satisfaction)


### Outer Loop

- [] Implement student model
- [] Choose questions, given knowledge of student's misconceptions (ie - student model)
    - This shouldbe some kind of hybrid recommender system (1. What do you think you need help with, 2. What do we know you don't understand)
    - But, how do we determine what a question tests (ie -- if a student has some misconception, how do we build a question that tests this? What about question difficulty?)
- Determine Interleaving behavior [!!]
- Determine distribution of questions, choose distractor from questions. [!!]
- [] Export report of learning