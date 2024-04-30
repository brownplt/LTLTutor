from flask import Flask, render_template, request
from ltlnode import parse_ltl_string
from codebook import getAllApplicableMisconceptions
from langtoltl import LTLTranslator
import os
import json
import requests
import random
import sys
import feedbackgenerator
import spotutils



app = Flask(__name__)


@app.before_first_request
def startup():
    try:
        with open('openai.secret.key', 'r') as file:
            secret_key = file.read().strip()
            os.environ['OPENAI_API_KEY'] = secret_key
    except:
        print("No Secret Key found", file=sys.stderr)

@app.route('/authorquestion', methods=['POST'])
def authorquestion():

    answer = request.form.get('answer')
    question = request.form.get('question')
    exercise_so_far = request.form.get('exercisesofar')

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
                "code": "Could not determine applicable distractors."
            })
        return render_template('authorquestion.html', distractors=distractors, error="", answer=answer, question=question, exerciseset = exercise_so_far)
    except Exception as e:
        distractors = [{
            "formula": "-",
            "code": "Invalid LTL formula"
        }]
        return render_template('authorquestion.html', error='Invalid LTL formula', distractors=distractors, answer=answer, question=question, exerciseset = exercise_so_far)



@app.route('/authorquestion', methods=['GET'])
def authorquestion_get():
    # Handle GET request
    distractors = []
    return render_template('authorquestion.html', distractors=distractors)



@app.route('/exercise', methods=['POST', 'GET'])
def exercise():
    ## Eventually, load this from a URL, that comes as part of the exercise
    path_to_json = os.path.join(app.static_folder, 'example_exercise.json')
    with open(path_to_json, 'r') as file:
        data = json.load(file)  # Load file content as JSON
    
    exercise_name = "DUMMY"

    ### We can come up with a better way to rearrange questions here ### 
    random.shuffle(data)

    return render_template('exercise.html', questions=data, exercise_name=exercise_name) 



@app.route('/getfeedback', methods=['POST'])
def loganswer():
    data = request.json




    # Generate feedback
    student_selection = data['selected_option']
    correct_answer = data['correct_option']
    isCorrect = data['correct']
    misconceptions = data['misconceptions']

    
    # We want to build the model here
    # Log to database

    to_return = {}


    if not isCorrect:
        # All responses are w.r.t the correct answer (that is -- correct answer subsumes ...)
        to_return = feedbackgenerator.getRelationship(correct_answer, student_selection)

        
        correct_traces = spotutils.generate_traces(correct_answer)
        incorrect_traces = spotutils.generate_traces(student_selection)

    return json.dumps(to_return)




@app.route('/log', methods=['POST'])
def log():
    data = request.json

    # TODO: Log to database

    print(data)
    return "OK"


if __name__ == '__main__':
    app.run()
