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
import random
import spotutils



port = os.getenv('PORT', default='5000')

app = Flask(__name__)

answer_logger = Logger()

DEFAULT_USERID = "defaultuser"
USERID_COOKIE = "ltluserid"


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ltl')
def ltl():
    return render_template('ltl.html')

@app.route('/loadfromjson')
def loadfromjson():
    return render_template('loadfromjson.html')

@app.route('/authorquestion/', methods=['POST'])
def authorquestion():

    kind = request.form.get('kind')
    answer = request.form.get('answer')
    question = request.form.get('question')
    exercise_so_far = request.form.get('exercisesofar')

    try:
        if kind == "tracesatisfaction_mc" or kind == "tracesatisfaction_yn":
            ltl = parse_ltl_string(question)


        elif kind == "englishtoltl":
            ltl = parse_ltl_string(answer)
        else:
            return "Invalid question type"
        
        

        ## TODO: Fix: getAllApplicableMisconceptions actually modifies ltl. 
        ## Solution is for it to deep copy somewhere.
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
        new_distractors = []
        added_traces = set([answer])
        ## IF the kind is trace satisfaction_mc, we need to generate traces for each distractor:
        if kind == "tracesatisfaction_mc" or kind == "tracesatisfaction_yn":
            # This is only true for trace_satisaction questions
            answer_formula = question
            
            for distractor in distractors:
                f = distractor['formula']
                potential_trace_choices = spotutils.generate_traces(f_accepted=f, f_rejected=answer_formula, max_traces=10)
                trace_choices = [t for t in potential_trace_choices if t not in added_traces]
                if len(trace_choices) > 0:
                    c = random.choice(trace_choices)
                    ms = distractor['code']
                    new_distractors.append({
                        'formula': c,
                        'code': ms
                    })
                    added_traces.add(c)
        

        distractors = new_distractors
        if len(distractors) == 0:
            distractors.append({
                "formula": "-",
                "code": "Could not determine applicable distractors."
            })



        return render_template('authorquestion.html', distractors=distractors, error="", answer=answer, question=question, exerciseset = exercise_so_far, kind = kind)
    
    
    except Exception as e:
        distractors = [{
            "formula": "-",
            "code": "Invalid LTL formula"
        }]
        return render_template('authorquestion.html', error='Invalid LTL formula', distractors=distractors, answer=answer, question=question, exerciseset = exercise_so_far, kind = kind)



@app.route('/authorquestion', methods=['GET'])
def authorquestion_get():
    # Handle GET request
    distractors = []
    return render_template('authorquestion.html', distractors=distractors)


@app.route('/exercise/predefined', methods=['POST'])
def exercise():
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
    return render_template('exercise.html', questions=data, exercise_name=exercise_name)



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
    elif questiontype == "trace_satisfaction_yn" or questiontype == "trace_satisfaction_mc":
        if not isCorrect:
            return "No further feedback currently available for Trace Satisfaction exercises."
    else:
        return "Something went wrong. No further feedback."



@app.route('/exercise/generate', methods=['GET'])
def newexercise():
    # Get a cookie from the request
    userId = request.cookies.get(USERID_COOKIE) or DEFAULT_USERID

    ### TODO: Should exercise involve only the literals the user has encountered? And a different # of literals
    LITERALS = ["r", "x", "y"]

    num_questions = random.randint(3, 8)

    ## TODO: Try and do better than this
    exercise_name = "Generated Exercise"
    
    user_logs = answer_logger.getUserLogs(userId=userId, lookback_days=30)
    exercise_builder = exercisebuilder.ExerciseBuilder(user_logs)

    data = exercise_builder.build_exercise(literals = LITERALS, num_questions = num_questions)
    return render_template('exercise.html', questions=data, exercise_name=exercise_name, literals = LITERALS)



@app.route('/getmy/<type>', methods=['GET'])
def viewstudentlogs(type):

    userId = request.cookies.get(USERID_COOKIE)
    if not userId:
        return "Could not identify user, no model available."
    
    logs = answer_logger.getUserLogs(userId=userId, lookback_days=30)

    if (type == "logs"):

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
    elif (type == "model"):
        exercise_builder = exercisebuilder.ExerciseBuilder(logs)
        model = exercise_builder.get_model()

        misconception_weights = model['misconception_weights']
        misconceptions_over_time = model['misconceptions_over_time']
        complexity = model['complexity']

        return render_template('model.html', complexity = complexity, misconception_weights = misconception_weights, misconceptions_over_time = misconceptions_over_time)
    else:
        return "Invalid type"
    

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(port))
