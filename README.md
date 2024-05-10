
## Running Server

To start a development web server at `http://localhost:5000/`
```
export FLASK_APP=app.py # set FLASK_APP=app.py on Windows
flask run
```

To deploy to Heroku:

```
heroku create <app-name> # Only do this once
git push heroku master
```

- To scale to 0 dynos (aka off): heroku ps:scale web=0 --app ltltutor
- To scale to a certain number of dynos: heroku ps:scale web=<n> --app ltltutor

- [] Currently, Heroku deployment isn't working because of SPOT installation


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