from flask import Flask, render_template, request, redirect, url_for, flash, current_app, Blueprint
from flask_login import login_required, current_user
from authroutes import Course, retrieve_course_data, get_owned_courses, login_required_as_courseinstructor
from logger import Logger
import json
import exercisebuilder
from collections import Counter, defaultdict


modelroutes = Blueprint('modelroutes', __name__)

logger = Logger()


def getLogsForUser(userId, lookback_days):
    logs = logger.getUserLogs(userId=userId, lookback_days=lookback_days)
    return logs



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
    exercises = logger.getUserExercises(userId=userId, lookback_days=365)
    to_return = {}
    for exercise in exercises:
        to_return[exercise.id] = {
            "user_id": exercise.user_id,
            "timestamp": exercise.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "exercise_data": exercise.exercise_data,
            "exercise_name": exercise.exerciseName
        }
    return render_template('studentexercises.html', exercises=to_return)



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
