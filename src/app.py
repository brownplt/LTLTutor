from flask import Flask, render_template, request
from ltlnode import parse_ltl_string
from codebook import getAllApplicableMisconceptions
from langtoltl import LTLTranslator
import os
import json
import requests
import random
import sys
from feedbackgenerator import FeedbackGenerator
import spotutils
from logger import Logger
import ast
from datetime import datetime


app = Flask(__name__)

answer_logger = Logger()

@app.before_first_request
def startup():
    try:
        with open('openai.secret.key', 'r') as file:
            secret_key = file.read().strip()
            os.environ['OPENAI_API_KEY'] = secret_key
    except:
        print("No Secret Key found", file=sys.stderr)


@app.route('/')
def index():
    return render_template('index.html')

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



@app.route('/exercise', methods=['POST'])
def exercise():


    sourceuri = request.form.get('sourceuri')
    if not sourceuri.endswith('.json'):
        return "Invalid sourceuri. Must end with .json"
    
    # Get the name of the JSON file from the URI
    exercise_name = os.path.basename(sourceuri) or "Exercise"
    exercise_name = exercise_name.replace('.json', '')

    if sourceuri.startswith('preload:'):
        sourceuri = sourceuri.replace('preload:', '')
        path_to_json = os.path.join(app.static_folder, sourceuri)
        with open(path_to_json, 'r') as file:
            data = json.load(file)  # Load file content as JSON
    else:
        # Load the exercise from the sourceuri
        response = requests.get(sourceuri)
        if response.status_code != 200:
            return "Error loading exercise"
        data = response.json()


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


    misconceptions = ast.literal_eval(data['misconceptions'])
    question_text = data['question_text']
    question_options = json.dumps(data['question_options'])

    ## TODO: Need to establish student ID and plough it through ## 
    answer_logger.logStudentResponse(studentId = 1, misconceptions = misconceptions, question_text = question_text, question_options = question_options, correct_answer = isCorrect)

    to_return = {}
    if not isCorrect:
        fgen = FeedbackGenerator(correct_answer, student_selection)
        to_return['subsumed'] = fgen.correctAnswerSubsumes()
        to_return['contained'] = fgen.correctAnswerContained()
        to_return['disjoint'] = fgen.disjoint()
        to_return['cewords'] = fgen.getCEWords()
    return json.dumps(to_return)




@app.route('/log', methods=['POST'])
def log():
    data = request.json

    # TODO: Log to database

    print(data)
    return "OK"


## TODO: Remove this eventually
@app.route('/viewstudentlogs/<id>', methods=['GET'])
def viewstudentlogs(id):

    student_id = int(id)

    logs = answer_logger.getStudentLogs(studentId=student_id, lookback_days=30)

    to_return = {}
    for log in logs:
        to_return[log.id] = {
            "student_id": log.student_id,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "misconception": log.misconception,
            "question_text": log.question_text,
            "question_options": log.question_options,
            "correct_answer": log.correct_answer
        }


    return json.dumps(to_return)


if __name__ == '__main__':
    app.run()
