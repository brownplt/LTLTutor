



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
- To scale to a certain number of dynos: heroku ps:scale web=1 --app ltltutor

(or n instead of 1)

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


- [] Move `userId` from Cookie to something else.
- [] Introduce a third question type:
  - [x] Yes/No trace satisfaction (add an explanation field also!)
  - [] However, how would we determine *misconception* if someone gets a trace where the correct answer was `Yes`, and someone says `No`? Do we just have *no* misconception?

### Outer Loop

- [] Complexity


## Engineering Debt

- While psycopg2-binary is convenient for development and avoids the need for PostgreSQL client libraries, it's not recommended for production due to potential issues with the statically linked libraries. However, it's generally fine for many use cases, especially in smaller projects or where environment control (like on personal or managed servers) limits easy installation of the regular psycopg2.

- MERMAID renders are bad, and often time out :(
  - I think the solution is here: See https://mermaid.js.org/config/usage.html?id=usage

