from flask import Flask, render_template, request, redirect, url_for, flash, current_app, Blueprint
from flask_login import login_required, current_user
from authroutes import Course, retrieve_course_data, get_owned_courses, login_required_as_courseinstructor
from logger import Logger
import json
import exercisebuilder
from collections import Counter


modelroutes = Blueprint('modelroutes', __name__)

logger = Logger()


def getLogsForUser(userId, lookback_days):
    logs = logger.getUserLogs(userId=userId, lookback_days=lookback_days)
    return logs


def _coerce_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == 'true'
    return bool(value)


def _format_score(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        return f"{value:.2f}".rstrip('0').rstrip('.')
    return str(value)


def _normalize_questions(parsed_exercise_data):
    if isinstance(parsed_exercise_data, list):
        return parsed_exercise_data, None

    if isinstance(parsed_exercise_data, dict):
        if isinstance(parsed_exercise_data.get('questions'), list):
            return parsed_exercise_data['questions'], None
        return [parsed_exercise_data], None

    return [], 'Exercise JSON was not a question list/object.'


def _build_exercise_view(exercise):
    exercise_name = exercise.exerciseName or 'Untitled Exercise'
    timestamp_str = exercise.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_epoch = int(exercise.timestamp.timestamp()) if exercise.timestamp else 0

    parse_error = None
    questions_raw = []
    if not exercise.exercise_data:
        parse_error = 'No exercise data was stored for this record.'
    else:
        try:
            parsed_data = json.loads(exercise.exercise_data)
            questions_raw, parse_error = _normalize_questions(parsed_data)
        except Exception as exc:
            parse_error = f'Could not parse exercise JSON: {exc}'

    type_counts = Counter()
    questions = []
    search_tokens = [exercise_name, exercise.user_id or '', timestamp_str]

    for idx, question in enumerate(questions_raw, start=1):
        if not isinstance(question, dict):
            question_text = str(question)
            question_type = 'Unknown'
            options = []
            trace = ''
            feedback = ''
            score = None
            trace_data = ''
        else:
            question_text = str(question.get('question') or question.get('prompt') or '')
            question_type = str(question.get('type') or 'Unknown')
            options_raw = question.get('options') if isinstance(question.get('options'), list) else []
            options = []
            for option in options_raw:
                if isinstance(option, dict):
                    misconceptions_raw = option.get('misconceptions')
                    if isinstance(misconceptions_raw, list):
                        misconceptions = [str(item) for item in misconceptions_raw if item is not None]
                    elif misconceptions_raw is None or misconceptions_raw == '':
                        misconceptions = []
                    else:
                        misconceptions = [str(misconceptions_raw)]

                    option_view = {
                        'option_text': str(option.get('option') or ''),
                        'is_correct': _coerce_bool(option.get('isCorrect', False)),
                        'misconceptions': misconceptions,
                        'generated_from_formula': str(option.get('generatedFromFormula') or ''),
                        'trace_data': option.get('trace_data') or ''
                    }
                else:
                    option_view = {
                        'option_text': str(option),
                        'is_correct': False,
                        'misconceptions': [],
                        'generated_from_formula': '',
                        'trace_data': ''
                    }

                options.append(option_view)
                search_tokens.append(option_view['option_text'])
                if option_view['generated_from_formula']:
                    search_tokens.append(option_view['generated_from_formula'])
                if option_view['misconceptions']:
                    search_tokens.extend(option_view['misconceptions'])

            trace = str(question.get('trace') or '')
            feedback = str(question.get('feedback') or '')
            score = _format_score(question.get('score'))
            trace_data = question.get('trace_data') or ''

        type_counts[question_type] += 1

        question_view = {
            'index': idx,
            'question_text': question_text or f'Question {idx}',
            'question_type': question_type,
            'score': score,
            'trace': trace,
            'feedback': feedback,
            'trace_data': trace_data,
            'options': options,
            'option_count': len(options),
            'correct_option_count': len([option for option in options if option['is_correct']])
        }
        questions.append(question_view)

        search_tokens.extend([
            question_view['question_text'],
            question_view['question_type'],
            question_view['trace'],
            question_view['feedback']
        ])

    search_blob = ' '.join(token for token in search_tokens if token).lower()
    question_types = sorted(type_counts.keys())

    return {
        'id': exercise.id,
        'user_id': exercise.user_id,
        'timestamp': timestamp_str,
        'timestamp_epoch': timestamp_epoch,
        'exercise_name': exercise_name,
        'exercise_data': exercise.exercise_data or '',
        'parse_error': parse_error,
        'questions': questions,
        'question_count': len(questions),
        'question_type_counts': dict(type_counts),
        'question_types': question_types,
        'search_blob': search_blob
    }



@modelroutes.route('/profile', methods=['GET'])
@login_required
def profile():
    LOOKBACK_DAYS = 365
    uid = current_user.username
    logs = getLogsForUser(uid, LOOKBACK_DAYS)

    num_logs = len(logs)

    num_correct = len([log for log in logs if log.correct_answer == 'True' or log.correct_answer == True or log.correct_answer == 'true'])

    exercise_builder = exercisebuilder.ExerciseBuilder(logs)
    model = exercise_builder.get_model()

    complexity = model['complexity']
    misconception_weights_over_time = model['misconception_weights_over_time']
    misconception_trends = model.get('misconception_trends', {})

    ## I want to remove 'MisconceptionCode.' from the keys of misconception_weights_over_time
    misconception_weights_over_time = {key.replace('MisconceptionCode.', ''): value for key, value in misconception_weights_over_time.items()}
    misconception_trends = {key.replace('MisconceptionCode.', ''): value for key, value in misconception_trends.items()}


    return render_template('student/profile.html', uid= uid, complexity = complexity, misconception_weights_over_time = misconception_weights_over_time, misconception_trends = misconception_trends, lookback_days = LOOKBACK_DAYS, num_answered = num_logs, num_correct = num_correct)




@modelroutes.route('/view/logs', methods=['GET'])
@login_required
def viewstudentlogs():
    userId = current_user.username
    logs = getLogsForUser(userId, 365)

    logs_dict = {}
    for log in logs:
        logs_dict[log.id] = {
            "user_id": log.user_id,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "misconception": log.misconception,
            "question_text": log.question_text,
            "question_options": log.question_options,
            "correct_answer": log.correct_answer,
            "mp_class": log.mp_class,
            "exercise": log.exercise,
            "course": log.course
        }
    return render_template('studentlogs.html', logs=logs_dict)
    


@modelroutes.route('/view/generatedexercises', methods=['GET'])
@login_required
def viewexercise():
    userId = current_user.username
    db_exercises = logger.getUserExercises(userId=userId, lookback_days=365)

    raw_exercises = {}
    exercises = []
    for exercise in db_exercises:
        raw_exercises[exercise.id] = {
            'user_id': exercise.user_id,
            'timestamp': exercise.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'exercise_data': exercise.exercise_data,
            'exercise_name': exercise.exerciseName
        }
        exercises.append(_build_exercise_view(exercise))

    exercises = sorted(exercises, key=lambda ex: ex['timestamp_epoch'], reverse=True)
    question_types = sorted({question_type for ex in exercises for question_type in ex['question_types']})
    total_questions = sum(ex['question_count'] for ex in exercises)

    return render_template(
        'studentexercises.html',
        uid=userId,
        exercises=exercises,
        raw_exercises=raw_exercises,
        question_types=question_types,
        total_questions=total_questions
    )



@modelroutes.route('/view/responses/<course_name>', methods=['GET'])
@login_required_as_courseinstructor
def viewresponses(course_name):
    userId = current_user.username
    course = retrieve_course_data(course_name)

    ### Now make sure that the exercise is owned by the user.
    if course.owner != userId:
        return "You do not have access to this resource.", 401

    responses = logger.getCourseResponses(course_name=course_name)
    to_return = {}
    for response in responses:
        to_return[response.id] = {
            "user_id": response.user_id,
            "timestamp": response.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "misconception": response.misconception,
            "question_text": response.question_text,
            "question_options": response.question_options,
            "correct_answer": response.correct_answer,
            "question_type": response.question_type,
            "mp_class": response.mp_class,
            "exercise": response.exercise,
            "course": response.course
        }

    user_counts = Counter()
    user_correct = Counter()
    user_last = {}

    for resp in to_return.values():
        user = resp['user_id']
        user_counts[user] += 1
        if str(resp['correct_answer']).lower() == 'true':
            user_correct[user] += 1
        user_last[user] = max(user_last.get(user, ''), resp['timestamp'])

    histogram = sorted(user_counts.items(), key=lambda x: x[1], reverse=True)

    misconception_counts = Counter()
    for resp in to_return.values():
        misconception = resp['misconception']
        if misconception:
            misconception_counts[misconception] += 1

    misconception_histogram = misconception_counts.most_common()

    return render_template(
        'courseresponses.html',
        responses=to_return,
        course_name=course_name,
        user_counts=user_counts,
        user_correct=user_correct,
        user_last=user_last,
        histogram=histogram,
        misconception_histogram=misconception_histogram
    )
