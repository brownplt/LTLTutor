
from flask import Flask, render_template, request, redirect, url_for, flash, current_app, Blueprint
from flask_login import login_required, current_user
from authroutes import Course, retrieve_course_data, get_owned_courses
from logger import Logger
import json
import exercisebuilder


modelroutes = Blueprint('modelroutes', __name__)

logger = Logger()


def getLogsForUser(userId):
    logs = logger.getUserLogs(userId=userId, lookback_days=30)
    return logs

@modelroutes.route('/view/logs', methods=['GET'])
@login_required
def viewstudentlogs():
    userId = current_user.username
    logs = getLogsForUser(userId)
    to_return = {}
    for log in logs:
        to_return[log.id] = {
            "user_id": log.user_id,
            "timestamp": log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "misconception": log.misconception,
            "question_text": log.question_text,
            "question_options": log.question_options,
            "correct_answer": log.correct_answer,
            "mp_class": log.mp_class,
            "exercise": log.exercise
        }
    return json.dumps(to_return)


## TODO: This is definitely a work in progress, and not what we want.
@modelroutes.route('/view/model', methods=['GET'])
@login_required
def viewmodel():
    uid = current_user.username
    logs = getLogsForUser(uid)
    exercise_builder = exercisebuilder.ExerciseBuilder(logs)
    model = exercise_builder.get_model()
    misconception_weights = model['misconception_weights']
    misconceptions_over_time = model['misconceptions_over_time']

    ### TODO: Make this misconception weights over time or something?

    # I want to make sure that if a misconception is not present for a given timestamp,
    # it's value for that timestamp is 0.
    # So I need to fill in the gaps in the dictionary.
    # I will do this by iterating over all timestamps and adding the missing ones.
    all_timestamps = set()
    for key, value in misconceptions_over_time.items():
        for dt, freq in value:
            all_timestamps.add(dt)

    # Then, for each misconception, I will add the missing timestamps with a frequency of 0.
    for key, value in misconceptions_over_time.items():
        for dt in all_timestamps:
            if dt not in [dt for dt, freq in value]:
                value.append((dt, 0))

    for key, value in misconceptions_over_time.items():
        misconceptions_over_time[key] = [(dt.timestamp(), freq) for dt, freq in value]


    complexity = model['complexity']

    return render_template('model.html', uid = uid, complexity = complexity, misconception_weights = misconception_weights, misconceptions_over_time = misconceptions_over_time)
    
@modelroutes.route('/view/generatedexercises', methods=['GET'])
@login_required
def viewexercise():
    userId = current_user.username
    exercises = logger.getUserExercises(userId=userId, lookback_days=30)
    to_return = {}
    for exercise in exercises:
        to_return[exercise.id] = {
            "user_id": exercise.user_id,
            "timestamp": exercise.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "exercise_data": exercise.exercise_data,
            "exercise_name": exercise.exerciseName
        }
    return json.dumps(to_return)


@modelroutes.route('/view/responses/<exercise_name>', methods=['GET'])
@login_required
def viewexerciseresponses(exercise_name):
    userId = current_user.username
    exercise = retrieve_course_data(exercise_name)

    ### Now make sure that the exercise is owned by the user.
    if exercise.owner != userId:
        return "You do not have access to this resource.", 401

    responses = logger.getExerciseResponses(exercise_name)
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
            "exercise": response.exercise
        }
    return json.dumps(to_return)



