from flask import Flask, render_template, request
from ltlnode import parse_ltl_string
from codebook import getAllApplicableMisconceptions
from langtoltl import LTLTranslator
import os

app = Flask(__name__)


@app.before_first_request
def startup():
    with open('openai.secret.key', 'r') as file:
        secret_key = file.read().strip()
        os.environ['OPENAI_API_KEY'] = secret_key

@app.route('/qgen', methods=['POST'])
def qgen():
    ########
    # question = request.form.get('question')
    # trans = LTLTranslator()
    # LTLsuggestions = trans.natural_lang_to_ltl(question)
    # #######

    answer = request.form.get('answer')

    # Parse the LTL string
    try:
        ltl = parse_ltl_string(answer)
        d = getAllApplicableMisconceptions(ltl)
        distractors = []
        for misconception in d:
            distractors.append({
                "formula": str(misconception.node),
                "code": str(misconception.misconception)
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




# @app.route('/translate', methods=['POST'])
# def translate():
#     trans = LTLTranslator()
#     string_to_translate = request.form.get('question')
    
#     LTLsuggestions = trans.natural_lang_to_ltl(string_to_translate)
#     return asLTL



if __name__ == '__main__':
    app.run()
