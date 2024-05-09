
## Running Server

To start a development web server at `http://localhost:5000/`
```
export FLASK_APP=app.py # set FLASK_APP=app.py on Windows
flask run
```

## Re-Generating Parser from ANTLR
```
antlr4 -Dlanguage=Python3 ltl.g4
```

## Running tests






# TODO:


### Inner Loop
- [] Question generation
    - [] Generate answer from Natural Language (Maybe using `nl2ltl`)
- [] LTL -> Natural Language

- [] Improve distractor generator. Currently so-so.
- [] Move `userId` from Cookie to something else.

### Outer Loop


- Determine Interleaving behavior
   - [] Interleave question types
- Determine distribution of questions, choose distractor from questions (if possible?)
  - [] Export report of learning
- [] Complexity