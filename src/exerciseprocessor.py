import random
import os
import requests
import json
import spotutils


def load_questions_from_sourceuri(sourceuri, staticfolderpath):
    if sourceuri.startswith('preload:'):
        sourceuri = sourceuri.replace('preload:', '')
        path_to_json = os.path.join(staticfolderpath, sourceuri)
        with open(path_to_json, 'r') as file:
            return json.load(file)  
    else:
        response = requests.get(sourceuri)
        if response.status_code != 200:
            raise Exception("Error loading exercise")
        return response.json()


def randomize_questions(data):
    # Randomize question order
    random.shuffle(data)
    # Randomize option order
    for k in data:
        xs = k['options']
        random.shuffle(xs)
        k['options'] = xs
    return data


def question_eng2ltl_to_tracesatisfaction(question):

    tracesat_question = {}

    nat_lang = question['question']
    options = question['options']
    newoptions = []

    correct_options = [option for option in options if option['isCorrect']]

    assert len(correct_options) == 1 # there should be exactly one correct option
    correct_option = correct_options[0]
    tracesat_question['question'] = correct_option['option']
    newoptions = []
    for option in options:
        f = option['option']
        isCorrect = option['isCorrect']
        misconceptions = option['misconceptions']

        if isCorrect: 
            trace_choices = spotutils.generate_accepted_traces(f)
        else:
            trace_choices = spotutils.generate_traces(f_accepted=f, f_rejected=correct_option['option'])
        
        if len(trace_choices) == 0:

            ## TODO: We should generate a random trace here!

            continue
        else:
            newoptions.append( {
                'option': random.choice(trace_choices),
                'isCorrect': isCorrect,
                'misconceptions': misconceptions
            })
    tracesat_question['options'] = newoptions
    return tracesat_question

def exercise_eng2ltl_to_tracesatisfaction(exercise):
    questions = [question_eng2ltl_to_tracesatisfaction(question) for question in exercise] 
    return questions