from flask import Flask, render_template, request, Blueprint, jsonify, redirect
from flask_login import login_required, current_user


from ltlnode import parse_ltl_string, SUPPORTED_SYNTAXES
from codebook import getAllApplicableMisconceptions
import os
import json
import sys
import csv
from difflib import SequenceMatcher
from markupsafe import Markup, escape
from feedbackgenerator import FeedbackGenerator
from logger import Logger
import ast
import exerciseprocessor
import exercisebuilder
import random
import spotutils
from itertools import chain
from collections import Counter, defaultdict
import uuid
import requests
from stepper import traceSatisfactionPerStep
import ltltoeng
from authroutes import (
    authroutes,
    init_app,
    retrieve_course_data,
    get_owned_courses,
    login_required_as_courseinstructor,
    getUserCourse,
    get_course_students,
    get_exercises_for_course,
)
from modelroutes import modelroutes











port = os.getenv('PORT', default='5000')

app = Flask(__name__)


@app.before_request
def enforce_https_in_production():
    """Redirect to HTTPS on Heroku deployments while allowing local development."""
    host = request.host.split(":", 1)[0]
    if host in {"localhost", "127.0.0.1"}:
        return

    forwarded_proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    if forwarded_proto != "https":
        secure_url = request.url.replace("http://", "https://", 1)
        return redirect(secure_url, code=301)

answer_logger = Logger()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

BENCHMARK_FILES = {
    "near": os.path.join(PROJECT_ROOT, "semantic_benchmark_near_eng.csv"),
    "far": os.path.join(PROJECT_ROOT, "semantic_benchmark_far_eng.csv"),
}


def _load_benchmark_rows():
    data = {}
    for label, path in BENCHMARK_FILES.items():
        if not os.path.exists(path):
            data[label] = []
            continue

        with open(path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = []
            for idx, row in enumerate(reader):
                rows.append({
                    "row_index": idx,
                    "ltl_formula": row.get("ltl_formula", ""),
                    "english_translation": row.get("english_translation", ""),
                    "closest_mutant_formula": row.get("closest_mutant_formula", ""),
                    "closest_mutant_english": row.get("closest_mutant_english", ""),
                    "closest_mutant_misconception": row.get("closest_mutant_misconception", ""),
                    "closest_distance": float(row.get("closest_distance", 0) or 0),
                    "max_distance": float(row.get("max_distance", 0) or 0),
                    "avg_distance": float(row.get("avg_distance", 0) or 0),
                    "num_mutants": int(float(row.get("num_mutants", 0) or 0)),
                    "dataset": label
                })
            data[label] = rows
    return data


BENCHMARK_ROWS = _load_benchmark_rows()


def _highlight_differences(text_a, text_b):
    tokens_a = text_a.split()
    tokens_b = text_b.split()
    matcher = SequenceMatcher(None, tokens_a, tokens_b)
    opcodes = matcher.get_opcodes()

    def build(tokens, use_a):
        parts = []
        for tag, i1, i2, j1, j2 in opcodes:
            segment = tokens[i1:i2] if use_a else tokens[j1:j2]
            if not segment:
                continue
            escaped = " ".join(escape(token) for token in segment)
            if tag == 'equal':
                parts.append(escaped)
            else:
                parts.append(f"<mark>{escaped}</mark>")
        return Markup(" ".join(parts))

    return build(tokens_a, True), build(tokens_b, False)


def _next_index_for_dataset(user_id, dataset):
    rows = BENCHMARK_ROWS.get(dataset, [])
    rated = answer_logger.getRatedSentencePairIndices(user_id, dataset)
    for idx in range(len(rows)):
        if idx not in rated:
            return idx
    return None


def _pick_next_pair(user_id):
    options = []
    next_near = _next_index_for_dataset(user_id, "near")
    next_far = _next_index_for_dataset(user_id, "far")

    if next_near is not None:
        options.append(("near", next_near))
    if next_far is not None:
        options.append(("far", next_far))

    if not options:
        return None, None, None

    if len(options) == 2:
        dataset = random.choice(["near", "far"])
        index = next_near if dataset == "near" else next_far
    else:
        dataset, index = options[0]

    row = BENCHMARK_ROWS[dataset][index]
    return dataset, index, row


def getUserName():
    return current_user.username

def getUserId():
    return current_user.id

    

@app.template_filter('flatten')
def flatten(lst):
    return list(chain.from_iterable(lst))

app.jinja_env.filters['flatten'] = flatten


@app.template_filter('fromjson')
def fromjson_filter(s):
    """Parse a JSON string into a Python object"""
    try:
        return json.loads(s) if s else []
    except (json.JSONDecodeError, TypeError):
        return []

app.jinja_env.filters['fromjson'] = fromjson_filter


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

    num_logs = len(logs)
    num_correct = len([log for log in logs if str(log.correct_answer).lower() == 'true'])

    exercise_builder = exercisebuilder.ExerciseBuilder(logs)
    model = exercise_builder.get_model()
    misconception_weights = model['misconception_weights']
    misconception_count = model['misconception_count']


    # For all the keys of misconception_weights, remove the prefix MisconceptionCode. if it is present
    misconception_weights = {k.replace("MisconceptionCode.", ""): v for k, v in misconception_weights.items()}


    ##########
    ## With the introduction of syntactic distractor experiments,
    ## we may have misconception explainers that do not have a corresponding file in the 'misconceptionexplainers' directory.
    ## The only one we expect is 'syntactic.html'.
    ## So we need to check if the file exists in the directory before joining it with the 'misconceptionexplainers' directory.

    red_herring = "syntactic"

    ranked_misconceptions = sorted(misconception_weights.items(), key=lambda item: item[1], reverse=True)
    # And remove the red herring from ranked_misconceptions
    ranked_misconceptions = [item for item in ranked_misconceptions if (item[0]).lower() != red_herring]
    top_two_misconceptions = ranked_misconceptions[:2]

    ########

    # Convert the top two misconceptions back to a dictionary
    top_two_misconceptions = dict(top_two_misconceptions)
    # Convert the keys to lowercase and add '.html' to the end
    top_two_misconceptions = [k.lower() + '.html' for k, v in top_two_misconceptions.items()]



    # Join the keys with the 'misconceptionexplainers' directory
    top_two_misconceptions = [os.path.join('misconceptionexplainers', k) for k in top_two_misconceptions]





    # Now choose one of the top two misconceptions randomly
    max_misconception = random.choice(top_two_misconceptions)
    
    # Get course exercises if user is a course student
    course_exercises = []
    completed_exercises = set()
    user_course = getUserCourse(userId)
    if user_course:
        course_exercises = get_exercises_for_course(user_course)
        
        # Check which exercises the user has completed
        if course_exercises:
            exercise_counts = []
            for ex in course_exercises:
                questions = json.loads(ex.exercise_json) if ex.exercise_json else []
                exercise_counts.append((ex.name, len(questions)))
            completed_exercises = answer_logger.getCompletedExercises(userId, exercise_counts)
    
    return render_template(
        'index.html',
        uid=getUserName(),
        misconception_weights=misconception_weights,
        misconception_count=misconception_count,
        max_misconception=max_misconception,
        num_logs=num_logs,
        num_correct=num_correct,
        user_course=user_course,
        course_exercises=course_exercises,
        completed_exercises=completed_exercises
    )

@app.route('/ltl')
def ltl():
    return render_template('ltl.html', uid = getUserName())

@app.route('/loadfromjson')
def loadfromjson():
    return render_template('loadfromjson.html', uid = getUserName())

@app.route('/ltltoeng', methods=['GET'])
def ltl_to_english():
    """Lightweight endpoint to translate an LTL formula to English for testing."""
    formula = request.args.get('formula', '').strip()
    if not formula:
        return jsonify({"error": "Missing required query parameter 'formula'."}), 400
    try:
        node = parse_ltl_string(formula)
        english = ltltoeng.finalize_sentence(node.__to_english__())
    except Exception as e:
        return jsonify({"error": "Failed to translate formula.", "details": str(e)}), 400


@app.route('/ltltoeng/rating', methods=['GET', 'POST'])
@login_required
def ltltoeng_rating():
    user_id = getUserName()
    rated_near = answer_logger.getRatedSentencePairIndices(user_id, "near")
    rated_far = answer_logger.getRatedSentencePairIndices(user_id, "far")

    progress = {
        "near": {"done": len(rated_near), "total": len(BENCHMARK_ROWS.get("near", []))},
        "far": {"done": len(rated_far), "total": len(BENCHMARK_ROWS.get("far", []))}
    }

    if request.method == 'POST':
        dataset = request.form.get('dataset', '')
        row_index = request.form.get('row_index', '')
        likert_value = request.form.get('likert', '')
        awkward_flag = request.form.get('awkward_flag') == 'on'
        awkward_notes = request.form.get('awkward_notes', '').strip()

        try:
            row_index = int(row_index)
            likert_rating = int(likert_value)
        except ValueError:
            return jsonify({"error": "Invalid rating payload"}), 400

        if likert_rating < 1 or likert_rating > 5:
            return jsonify({"error": "Likert rating must be between 1 and 5"}), 400

        rows = BENCHMARK_ROWS.get(dataset)
        if rows is None or row_index < 0 or row_index >= len(rows):
            return jsonify({"error": "Unknown benchmark item"}), 400

        pair = rows[row_index]

        answer_logger.logSentencePairRating({
            "user_id": user_id,
            "dataset": dataset,
            "row_index": row_index,
            "base_english": pair["english_translation"],
            "mutant_english": pair["closest_mutant_english"],
            "base_ltl": pair["ltl_formula"],
            "mutant_ltl": pair["closest_mutant_formula"],
            "misconception": pair["closest_mutant_misconception"],
            "likert_rating": likert_rating,
            "awkward_flag": awkward_flag,
            "awkward_notes": awkward_notes,
            "closest_distance": pair["closest_distance"],
            "max_distance": pair["max_distance"],
            "avg_distance": pair["avg_distance"],
            "num_mutants": pair["num_mutants"],
        })

        return redirect('/ltltoeng/rating')

    dataset, row_index, pair = _pick_next_pair(user_id)
    if pair is None:
        return render_template(
            'ltltoeng_rating.html',
            uid=user_id,
            done=True,
            progress=progress
        )

    highlighted_base, highlighted_mutant = _highlight_differences(pair["english_translation"], pair["closest_mutant_english"])

    return render_template(
        'ltltoeng_rating.html',
        uid=user_id,
        done=False,
        pair=pair,
        dataset=dataset,
        row_index=row_index,
        highlighted_base=highlighted_base,
        highlighted_mutant=highlighted_mutant,
        progress=progress
    )

    return jsonify({"formula": formula, "english": english})


@app.route('/ltltoeng/ui', methods=['GET', 'POST'])
@login_required
def ltl_to_english_ui():
    """Simple HTML interface to translate an LTL formula to English."""
    translation = None
    error = None
    input_formula = ""

    if request.method == 'POST':
        input_formula = request.form.get('formula', '').strip()
        if not input_formula:
            error = "Please enter an LTL formula."
        else:
            try:
                node = parse_ltl_string(input_formula)
                translation = ltltoeng.finalize_sentence(node.__to_english__())
            except Exception as e:
                error = f"Failed to translate formula: {e}"

    return render_template(
        'ltltoengui.html',
        uid=getUserName(),
        translation=translation,
        error=error,
        input_formula=input_formula,
    )

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
                    c = spotutils.weighted_trace_choice(trace_choices)
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

    course_summaries = []
    for course in authored:
        responses = answer_logger.getCourseResponses(course.name)

        misconception_counter = Counter([
            resp.misconception for resp in responses if resp.misconception
        ])
        top_misconceptions = misconception_counter.most_common(3)

        responses_by_exercise_user = defaultdict(lambda: defaultdict(int))
        for resp in responses:
            if resp.exercise:
                responses_by_exercise_user[resp.exercise][resp.user_id] += 1

        exercise_completion = []
        course_exercises = get_exercises_for_course(course.name)
        for ex in course_exercises:
            questions = json.loads(ex.exercise_json) if ex.exercise_json else []
            question_count = len(questions)
            user_counts = responses_by_exercise_user.get(ex.name, {})
            started = len(user_counts)
            completed = len([
                user for user, count in user_counts.items()
                if question_count > 0 and count >= question_count
            ])

            exercise_completion.append({
                'name': ex.name,
                'question_count': question_count,
                'started': started,
                'completed': completed
            })

        students = get_course_students(course.name)
        student_usernames = [student.username for student in students]

        course_summaries.append({
            'name': course.name,
            'response_count': len(responses),
            'students': student_usernames,
            'top_misconceptions': top_misconceptions,
            'exercise_completion': exercise_completion
        })

    return render_template(
        'instructorhome.html',
        uid=userId,
        owned_course_names=owned_course_names,
        course_summaries=course_summaries
    )





@app.route('/exercise/load/<exercise_name>', methods=['GET'])
@login_required
def exercise(exercise_name):
    """Load an exercise by name - checks instructor exercises first, then falls back to course-based lookup"""
    # First, try to find instructor exercises for a course with this name
    exercises = get_exercises_for_course(exercise_name)
    
    if exercises and len(exercises) > 0:
        # Use the first exercise assigned to this course
        exercise_obj = exercises[0]
        try:
            data = json.loads(exercise_obj.exercise_json)
            data = exerciseprocessor.randomize_questions(data)
            
            # Extract literals for trace expansion
            literals = set()
            for q in data:
                if 'question' in q:
                    try:
                        literals.update(exerciseprocessor.getFormulaLiterals(q['question']))
                    except:
                        pass
            
            data = exerciseprocessor.change_traces_to_mermaid(data, literals=list(literals))
            return render_template('exercise.html', uid=getUserName(), questions=data, exercise_name=exercise_obj.name)
        except Exception as e:
            return f"Error loading exercise: {str(e)}"
    
    # Fall back to old behavior - check if there's course data
    course = retrieve_course_data(exercise_name)
    if not course:
        return f"Exercise or course '{exercise_name}' not found."
    
    # Course exists but has no exercises assigned
    return f"No exercises found for course '{exercise_name}'. Ask your instructor to assign exercises."



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


@app.route('/exercise/predefined', methods=['GET', 'POST'])
@login_required
def exercise_predefined_get():
    """Load an exercise from a sourceuri (preload:, instructor:, or URL)"""
    if request.method == 'GET':
        sourceuri = request.args.get('sourceuri')
    else:
        sourceuri = request.form.get('sourceuri')
    
    if not sourceuri:
        return redirect('/loadfromjson')
    
    try:
        data = exerciseprocessor.load_questions_from_sourceuri(sourceuri, app.static_folder)
        data = exerciseprocessor.randomize_questions(data)
        
        # Try to extract literals from questions for trace expansion
        literals = set()
        for q in data:
            if q.get('type') == 'englishtoltl':
                # Get literals from correct answer
                for opt in q.get('options', []):
                    if opt.get('isCorrect'):
                        try:
                            literals.update(exerciseprocessor.getFormulaLiterals(opt['option']))
                        except:
                            pass
            elif 'question' in q:
                # For trace questions, try to parse the formula
                try:
                    literals.update(exerciseprocessor.getFormulaLiterals(q['question']))
                except:
                    pass
        
        data = exerciseprocessor.change_traces_to_mermaid(data, literals=list(literals) if literals else [])
        
        # Generate exercise name from sourceuri
        exercise_name = sourceuri.split(':')[-1].replace('.json', '').replace('_', ' ').title()
        
    except Exception as e:
        print(f"Error loading exercise from {sourceuri}: {e}")
        return f"Error loading exercise: {str(e)}"
    
    return render_template('exercise.html', uid=getUserName(), questions=data, exercise_name=exercise_name)


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
        return render_template('stepper.html', uid = getUserName(), error="", prefixstates=[], cyclestates=[], matrix_data={"subformulae": [], "matrix": [], "rows": []})

    if request.method == 'POST':
        ltl = request.form.get('formula')
        trace = request.form.get('trace')
        if ltl == "" or trace == "":
            error="Please enter an LTL formula and a trace."
        
    try:
        node = parse_ltl_string(ltl)
    except:
        return render_template('stepper.html', uid = getUserName(), error="Invalid LTL formula " + ltl, prefixstates=[], cyclestates=[], matrix_data={"subformulae": [], "matrix": [], "rows": []})

    try:
        result = traceSatisfactionPerStep(node = node, trace = trace, syntax = syntax_choice)
    except:
        return render_template('stepper.html', uid = getUserName(), error="Invalid trace " + trace, prefixstates=[], cyclestates=[], matrix_data={"subformulae": [], "matrix": [], "rows": []})
    
    matrix_data = result.getMatrixView()
    return render_template('stepper.html', uid = getUserName(), error="", prefixstates=result.prefix_states, cyclestates=result.cycle_states, formula = ltl, trace=trace, matrix_data=matrix_data)


##### Eng LTL Logging Routes ###
@app.route('/logenglishltlrating', methods=['POST'])
@login_required
def logenglishltlrating():
    data = request.json
    userId = getUserName()
    english = data.get('english', '')
    ltl = data.get('ltl', '')
    comments = data.get('issues', '') or ''
    suggested_translation = data.get('suggested_translation', '').strip()

    if suggested_translation:
        if comments:
            comments = f"{comments} | Suggested translation: {suggested_translation}"
        else:
            comments = f"Suggested translation: {suggested_translation}"

    e_ltl_pair = {
        "english": english,
        "ltl": ltl,
        "comments": comments,
        "user_id": userId
    }


    answer_logger.recordEnglishLTLPair(e_ltl_pair)
    return { "message": "Success" }


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(port))
