from flask import Flask, render_template, request, Blueprint
from flask_login import login_required, current_user


from ltlnode import parse_ltl_string, SUPPORTED_SYNTAXES
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
from itertools import chain
import uuid
import requests
from stepper import traceSatisfactionPerStep
from authroutes import authroutes, init_app, retrieve_course_data, get_owned_courses, login_required_as_courseinstructor, getUserCourse
from modelroutes import modelroutes











port = os.getenv('PORT', default='5000')

app = Flask(__name__)

answer_logger = Logger()


def getUserName():
    return current_user.username

def getUserId():
    return current_user.id

    

@app.template_filter('flatten')
def flatten(lst):
    return list(chain.from_iterable(lst))

app.jinja_env.filters['flatten'] = flatten


sk = os.environ.get('SECRET_KEY')
app.secret_key = sk


init_app(app)
app.register_blueprint(authroutes)
app.register_blueprint(modelroutes)


@app.route('/')
@login_required
def index():
    userId = getUserName()
    if not userId:
        return render_template('index.html', uid = "Could not identify user. Are you logged in?")
    
    logs = answer_logger.getUserLogs(userId=userId, lookback_days=30)
    exercise_builder = exercisebuilder.ExerciseBuilder(logs)
    model = exercise_builder.get_model()
    misconception_weights = model['misconception_weights']
    misconception_count = model['misconception_count']


    # For all the keys of misconception_weights, remove the prefix MisconceptionCode. if it is present
    misconception_weights = {k.replace("MisconceptionCode.", ""): v for k, v in misconception_weights.items()}

    # Sort the misconception_weights dictionary by value in descending order and get the first 2 items
    top_two_misconceptions = sorted(misconception_weights.items(), key=lambda item: item[1], reverse=True)[:2]
    # Convert the top two misconceptions back to a dictionary
    top_two_misconceptions = dict(top_two_misconceptions)
    # Convert the keys to lowercase and add '.html' to the end
    top_two_misconceptions = [k.lower() + '.html' for k, v in top_two_misconceptions.items()]

    # Join the keys with the 'misconceptionexplainers' directory
    top_two_misconceptions = [os.path.join('misconceptionexplainers', k) for k in top_two_misconceptions]

    # Now choose one of the top two misconceptions randomly
    max_misconception = random.choice(top_two_misconceptions)   
    return render_template('index.html',uid = getUserName(), misconception_weights = misconception_weights, misconception_count = misconception_count, max_misconception = max_misconception)

@app.route('/ltl')
def ltl():
    return render_template('ltl.html', uid = getUserName())

@app.route('/loadfromjson')
def loadfromjson():
    return render_template('loadfromjson.html', uid = getUserName())

@app.route('/authorquestion/', methods=['POST'])
@login_required
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



        return render_template('authorquestion.html', uid = getUserName(), distractors=distractors, error="", answer=answer, question=question, exerciseset = exercise_so_far, kind = kind)
    
    
    except Exception as e:
        distractors = [{
            "formula": "-",
            "code": "Invalid LTL formula"
        }]
        return render_template('authorquestion.html', uid = getUserName(), error='Invalid LTL formula', distractors=distractors, answer=answer, question=question, exerciseset = exercise_so_far, kind = kind)



@app.route('/authorquestion', methods=['GET'])
@login_required
def authorquestion_get():
    # Handle GET request
    distractors = []
    return render_template('authorquestion.html', uid = getUserName(), distractors=distractors)


########## Routes for exercises ##########


@app.route('/exercise/home', methods=['GET'])
@login_required
def exercisehome():
    userId = getUserName()

    return render_template('exercisehome.html', uid = getUserName())

@app.route('/instructor/home', methods=['GET'])
@login_required_as_courseinstructor
def instructorhome():
    userId = getUserName()
    authored = get_owned_courses(userId)
    owned_course_names = [course.name for course in authored]
    return render_template('instructorhome.html', uid = userId, owned_course_names=owned_course_names)





@app.route('/exercise/load/<exercise_name>', methods=['GET'])
@login_required
def exercise(exercise_name):   
    exercise = retrieve_course_data(exercise_name)
    ## Ensure that the exercise exists, else return an error
    if not exercise:
        return f"Exercise {exercise_name} not found."

    exercise_content = exercise.exercise_data

    try:
        data = json.loads(exercise_content)
        data = exerciseprocessor.randomize_questions(data)
        data = exerciseprocessor.change_traces_to_mermaid(data, literals = [])
    except:
        return f"Error loading exercise {exercise_name}"
    return render_template('exercise.html', uid = getUserName(), questions=data, exercise_name=exercise_name)



@app.route('/getfeedback/<questiontype>', methods=['POST'])
@login_required
def loganswer(questiontype):
    MP_FORMULA_KEY = 'formula_for_mp_class'
    EXERCISE_KEY = 'exercise'


    data = request.json
    student_selection = data['selected_option']
    correct_answer = data['correct_option']

    isCorrect = data['correct']

    misconceptions = ast.literal_eval(data['misconceptions'])
    question_text = data['question_text']
    question_options = json.dumps(data['question_options'])

    userId = getUserName()
    courseId = getUserCourse(userId)
    mp_class = ""
    mp_formula_literals = []
    # If response has a mp_class field, log it
    if MP_FORMULA_KEY in data:

        ## TODO: For this classification, we need to ensure we are in classic syntax.
        to_classify = str(parse_ltl_string(data[MP_FORMULA_KEY]))
        mp_class = spotutils.get_mana_pneulli_class(to_classify)
        mp_formula_literals = exerciseprocessor.getFormulaLiterals(to_classify)

    exercise = ""
    if EXERCISE_KEY in data:
        exercise = data[EXERCISE_KEY]


    answer_logger.logStudentResponse(userId = userId, misconceptions = misconceptions, question_text = question_text,
                                      question_options = question_options, correct_answer = isCorrect, 
                                      questiontype=questiontype, mp_class = mp_class, exercise = exercise, course = courseId)
    

    if questiontype == "english_to_ltl":
        to_return = {}
        if not isCorrect:

            correct_answer_spot_syntax = str(parse_ltl_string(correct_answer))
            student_selection_spot_syntax = str(parse_ltl_string(student_selection))

            fgen = FeedbackGenerator(correct_answer_spot_syntax, student_selection_spot_syntax)
            to_return['subsumed'] = fgen.correctAnswerSubsumes()
            to_return['contained'] = fgen.correctAnswerContained()
            to_return['disjoint'] = fgen.disjoint()
            to_return['equivalent'] = fgen.equivalent()
            


            to_return['cewords'] = [exerciseprocessor.expandSpotTrace(w, literals=list(mp_formula_literals)) for w in fgen.getCEWords()]
            to_return['mermaid'] = [exerciseprocessor.genMermaidGraphFromSpotTrace(sr) for sr in to_return['cewords']]
        return json.dumps(to_return)
    elif questiontype == "trace_satisfaction_yn" or questiontype == "trace_satisfaction_mc":
        if not isCorrect:
            return { "message": "No further feedback currently available for Trace Satisfaction exercises." } 
    else:
        return { "message": "INVALID QUESTION TYPE!!." }
    return { "message": "No further feedback." }



@app.route('/exercise/generate', methods=['GET'])
@login_required
def newexercise():


    syntax_choice = request.cookies.get('ltlsyntax')
    if syntax_choice == None or syntax_choice not in SUPPORTED_SYNTAXES:
        syntax_choice = 'Classic'


    userId = getUserName()


    
    def generate_new_name():
        WORDS = [
        "apple", "book", "chair", "dog", "elephant", "flag", "garden", "hat", "ice", 
        "juice", "kite", "lamp", "moon", "nest", "orange", "pencil", "queen", "rose", 
        "sun", "tree", "umbrella", "vase", "water", "xylophone", "yellow", "zebra", 
        "ant", "bird", "cloud", "dolphin", "egg"
        ]
        return random.choice(WORDS) + "-" + random.choice(WORDS) + "-" + str(uuid.uuid4())[:4]



    ### TODO: Should exercise involve only the literals the user has encountered? And a different # of literals
    literals_pool = list("abcdehijknpqstvz")
    num_literals = random.randint(2, 4)
    LITERALS = random.sample(literals_pool, num_literals)
    num_questions = random.randint(3, 8)

    
    try:
        exercise_name = "Exercise " + generate_new_name()
    except Exception as e:
        print("Error generating exercise name:", e)
        exercise_name = "Exercise"
    
    user_logs = answer_logger.getUserLogs(userId=userId, lookback_days=30)

    complexity = answer_logger.getComplexity(userId=userId)       
    exercise_builder = exercisebuilder.ExerciseBuilder(user_logs, syntax = syntax_choice) if complexity == None else exercisebuilder.ExerciseBuilder(user_logs, complexity=complexity, syntax = syntax_choice)

    data = exercise_builder.build_exercise(literals = LITERALS, num_questions = num_questions)
    data = exerciseprocessor.randomize_questions(data)
    data = exerciseprocessor.change_traces_to_mermaid(data, literals = LITERALS)

    answer_logger.recordGeneratedExercise(userId, json.dumps(data), exercise_name = exercise_name)

    return render_template('exercise.html', uid = getUserName(), questions=data, exercise_name=exercise_name)




@app.route('/entryexitticket/<ticket>')
@login_required
def entryexitticket(ticket):
    userId = getUserName()
    if not userId:
        return "USER ID IS NOT SET, PLEASE RELOAD THE PAGE."
    
    uidlen = len(userId)
    choices = ["preload:robotrain-odd.json", "preload:robotrain-even.json"]

    entry_index = uidlen % 2
    exit_index = (uidlen + 1) % 2

    if ticket == "entry":
        return robotrain(choices[entry_index], exercise_name = "robotrain-entry")
    elif ticket == "exit":
        return robotrain(choices[exit_index], exercise_name = "robotrain-exit")
    else:
        return "Invalid ticket type."     

def robotrain(sourceuri, exercise_name):
    try:
        data = exerciseprocessor.load_questions_from_sourceuri(sourceuri, app.static_folder)
        data = exerciseprocessor.randomize_questions(data)
        data = exerciseprocessor.change_traces_to_mermaid(data, literals = ["e", "h"])
    except Exception as e:
        print(e)
        return "Error loading exercise"
    return render_template('/prebuiltexercises/robotrain.html', uid = getUserName(), questions=data, exercise_name=exercise_name)


###### Stepper routes ######

@app.route('/stepper', methods=['GET', 'POST'])
def ltlstepper():


    ## Get the syntax choice from the cookie
    syntax_choice = request.cookies.get('ltlsyntax')
    if syntax_choice == None or syntax_choice not in SUPPORTED_SYNTAXES:
        syntax_choice = 'Classic'

    if request.method == 'GET':
        return render_template('stepper.html', uid = getUserName(), error="", prefixstates=[], cyclestates=[])

    if request.method == 'POST':
        ltl = request.form.get('formula')
        trace = request.form.get('trace')
        if ltl == "" or trace == "":
            error="Please enter an LTL formula and a trace."
        
    try:
        node = parse_ltl_string(ltl)
    except:
        return render_template('stepper.html', uid = getUserName(), error="Invalid LTL formula " + ltl, prefixstates=[], cyclestates=[])

    try:
        result = traceSatisfactionPerStep(node = node, trace = trace, syntax = syntax_choice)
    except:
        return render_template('stepper.html', uid = getUserName(), error="Invalid trace " + trace, prefixstates=[], cyclestates=[])
    return render_template('stepper.html', uid = getUserName(), error="", prefixstates=result.prefix_states, cyclestates=result.cycle_states, formula = ltl, trace=trace)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(port))
