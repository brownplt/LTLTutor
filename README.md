



## Running Server

To start a development web server at `http://localhost:5000/`
```
export FLASK_APP=app.py # set FLASK_APP=app.py on Windows
flask run
```

To deploy to Heroku:

```
heroku create <app-name> # Only do this once
git push heroku main
```

- To scale to 0 dynos (aka off): heroku ps:scale web=0 --app ltltutor
- To scale to a certain number of dynos: heroku ps:scale web=<n> --app ltltutor

- [] Currently, Heroku deployment isn't working because of SPOT installation
  - May have to use either the Conda buildpack: https://github.com/heroku-python/conda-buildpack
  - Or the APT buildpack: https://github.com/heroku/heroku-buildpack-apt


## Re-Generating Parser from ANTLR
```
antlr4 -Dlanguage=Python3 ltl.g4
```

## Running tests






# TODO:


### Inner Loop

- [] Improve distractor generator. Currently so-so.
  - [] FOr traces, ensure that each state specifies a truth value for each variable (1 --> all are true)
- [] Move `userId` from Cookie to something else.
- [] Introduce a third question type: Yes/No trace satisfaction (add an explanation field also!)
  - However, how would we determine *misconception* if someone gets a trace where the correct answer was `Yes`, and someone says `No`? Do we just have *no* misconception?

### Outer Loop
 
- Determine distribution of questions, choose distractor from questions (if possible?)
  - [] Export report of learning
- [] Complexity