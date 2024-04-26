from flask import Flask, render_template, request
from ltlnode import parse_ltl_string
from codebook import getAllApplicableMisconceptions

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/qgen', methods=['POST'])
def qgen():
    # Handle form POST request
    # Access form data using request.form
    
    answer = request.form.get('answer')

    # Parse the LTL string
    try:
        ltl = parse_ltl_string(answer)
        d = getAllApplicableMisconceptions(ltl)
        distractors = []
        for misconception in d:
            distractors.append({
                "formula": misconception.node.toString(),
                "code": misconception.misconception.toString()
            })

        # Merge labels for equal formulae
        mergedDistractors = []
        for distractor in distractors:
            existingDistractor = next((d for d in mergedDistractors if d['formula'] == distractor['formula']), None)
            if existingDistractor:
                existingDistractor['code'] += f", {distractor['code']}"
            else:
                mergedDistractors.append(distractor)
        distractors = mergedDistractors

        if len(distractors) == 0:
            distractors.append({
                "formula": "-",
                "code": "No applicable misconceptions"
            })
        return render_template('qgen.html', distractors=distractors, error="")
    except Exception as e:
        distractors = [{
            "formula": "-",
            "code": "Invalid LTL formula"
        }]
        return render_template('qgen.html', error='Invalid LTL formula', distractors=distractors)

@app.route('/qgen', methods=['GET'])
def qgen_get():
    # Handle GET request
    distractors = []
    return render_template('qgen.html', distractors=distractors)



if __name__ == '__main__':
    app.run()
