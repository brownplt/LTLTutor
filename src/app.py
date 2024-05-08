from flask import Flask, render_template, request
from ltlnode import parse_ltl_string
from codebook import getAllApplicableMisconceptions
import os
import json
import sys
from feedbackgenerator import FeedbackGenerator
from logger import Logger
import ast
import exerciseprocessor
import exercisebuilder

app = Flask(__name__)

answer_logger = Logger()


DEFAULT_USERID = "defaultuser"
USERID_COOKIE = "ltluserid"



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

@app.route('/ltl')
def ltl():
    return render_template('ltl.html')

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



@app.route('/exercise/<kind>', methods=['POST'])
def exercise(kind):
    sourceuri = request.form.get('sourceuri')
    if not sourceuri.endswith('.json'):
        return "Invalid sourceuri. Must end with .json"
    
    # Get the name of the JSON file from the URI
    exercise_name = os.path.basename(sourceuri) or "Exercise"
    exercise_name = exercise_name.replace('.json', '')
    exercise_name = exercise_name.replace('preload:', '')

    try:
        data = exerciseprocessor.load_questions_from_sourceuri(sourceuri, app.static_folder)

        data = exerciseprocessor.randomize_questions(data)
    except:
        return "Error loading exercise"

    if kind == "tracesatisfaction":
        data = exerciseprocessor.exercise_eng2ltl_to_tracesatisfaction(data)
        exercise_name = "Trace Satisfaction " + exercise_name
        return render_template('tracesatexercise.html', questions=data, exercise_name=exercise_name) 
    elif kind == "englishtoltl":
        exercise_name = "English to LTL " + exercise_name
        return render_template('engtoltlexercise.html', questions=data, exercise_name=exercise_name) 
    else:
        return "Unknown exercise type"


@app.route('/getfeedback/<questiontype>', methods=['POST'])
def loganswer(questiontype):


    data = request.json
    student_selection = data['selected_option']
    correct_answer = data['correct_option']
    isCorrect = data['correct']

    misconceptions = ast.literal_eval(data['misconceptions'])
    question_text = data['question_text']
    question_options = json.dumps(data['question_options'])

    userId = request.cookies.get(USERID_COOKIE) or DEFAULT_USERID

    ## TODO: Need to establish student ID and plough it through ## 
    answer_logger.logStudentResponse(userId = userId, misconceptions = misconceptions, question_text = question_text, question_options = question_options, correct_answer = isCorrect, questiontype=questiontype)


    if questiontype == "english_to_ltl":
        to_return = {}
        if not isCorrect:
            fgen = FeedbackGenerator(correct_answer, student_selection)
            to_return['subsumed'] = fgen.correctAnswerSubsumes()
            to_return['contained'] = fgen.correctAnswerContained()
            to_return['disjoint'] = fgen.disjoint()
            to_return['cewords'] = fgen.getCEWords()
        return json.dumps(to_return)
    elif questiontype == "trace_satisfaction":
        if not isCorrect:
            return "No further feedback currently available for Trace Satisfaction exercises."
    else:
        return "Something went wrong. No further feedback."



@app.route('/newexercise/<kind>', methods=['GET'])
def newexercise(kind):

    exercise_name = "Generated Exercise"
    
    # Get a cookie from the request
    userId = request.cookies.get(USERID_COOKIE) or DEFAULT_USERID

    
    user_logs = answer_logger.getUserLogs(userId=userId, lookback_days=30)
    ### First get that users logs from the database
    exercise_builder = exercisebuilder.ExerciseBuilder(user_logs)

    ### TODO: Exercise should involve the literals the user has encountered?
    data = exercise_builder.build_exercise(literals = ["r", "g", "b"], complexity = 10, num_questions = 2)


    
    ## TODO: 1 is top, 0 bottom


    if kind == "tracesatisfaction":
        data = exerciseprocessor.exercise_eng2ltl_to_tracesatisfaction(data)
        exercise_name = "Trace Satisfaction " + exercise_name
        return render_template('tracesatexercise.html', questions=data, exercise_name=exercise_name) 
    elif kind == "englishtoltl":
        exercise_name = "English to LTL " + exercise_name
        return render_template('engtoltlexercise.html', questions=data, exercise_name=exercise_name) 
    else:
        return "Unknown exercise type"


## TODO: Remove this eventually
@app.route('/viewstudentlogs/<id>', methods=['GET'])
def viewstudentlogs(id):

    logs = answer_logger.getUserLogs(userId=id, lookback_days=30)

    to_return = {}
    for log in logs:
        to_return[log.id] = {
            "user_id": log.student_id,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "misconception": log.misconception,
            "question_text": log.question_text,
            "question_options": log.question_options,
            "correct_answer": log.correct_answer
        }


    return json.dumps(to_return)



if __name__ == '__main__':
    app.run()
