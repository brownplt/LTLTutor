import spotutils
import datetime
from collections import defaultdict
import codebook
from codebook import MisconceptionCode
import ltlnode
import random
import string

class ExerciseBuilder:
    def __init__(self, userLogs):
        self.userLogs = userLogs
        self.DEFAULT_WEIGHT = 0.7
        self.ltl_priorities = spotutils.DEFAULT_LTL_PRIORITIES.copy()
   

    def aggregateLogs(self, bucketsizeinhours=1):
        # Create an empty dictionary to store the buckets
        buckets = defaultdict(lambda: defaultdict(int))

        # Iterate over the log entries
        for log in self.userLogs:
            # Parse the timestamp string into a datetime object
            timestamp = log.timestamp
            # Calculate the bucket for the log entry
            bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            bucket += datetime.timedelta(hours=(timestamp.hour % bucketsizeinhours))

            # Add the log entry to the corresponding bucket
            misconception = log.misconception
            buckets[bucket][misconception] += 1
        return buckets


    def calculate_misconception_weights(self):

        buckets = self.aggregateLogs()
        all_concepts = [str(misconception) for misconception in MisconceptionCode]


        concept_history = defaultdict(list)
        weights = {}

        # Organize misconceptions by bucket and sort by date
        for bucket, misconceptions in buckets.items():
            for misconception, frequency in misconceptions.items():
                concept_history[misconception].append((bucket, frequency))

        for concept, entries in concept_history.items():
            entries.sort()  # Sort by date
            weight = 0
            previous_frequency = 0

            for date, frequency in entries:
                hours_ago = (datetime.datetime.now() - date).total_seconds() / 3600
                recency_weight = 1 / (1 + hours_ago)  # Decay function

                # Check if frequency has increased or decreased
                if frequency < previous_frequency:
                    weight_change = -recency_weight * (previous_frequency - frequency)
                else:
                    weight_change = recency_weight * (frequency - previous_frequency)

                weight += weight_change
                previous_frequency = frequency

            weights[concept] = max(weight, 0)  # Ensure weights don't go negative


        ### We stick with the default otherwise ###
        # Assign a default weight to concepts that have never been encountered
        # for concept in all_concepts:
        #     if concept not in weights:
        #         weights[concept] = self.DEFAULT_WEIGHT  

        # Normalize the weights to the range [0, 1]


        ## No, we don't want to do that right?
        ## Rather, we want to increase if it increased, decrease otherwise, centered around 1
        ## Need to understand this mechanism
        max_weight = max(weights.values())
        for concept in weights:
            weights[concept] /= max_weight

        return weights

    def operatorToSpot(self, operator):
        if operator in ["&", "&&"]:
            return "and"
        elif operator in ["|", "||"]:
            return "or"
        elif operator in ["!", "not"]:
            return "not"
        elif operator in ["=>", "->"]:
            return "implies"
        elif operator in ["<=>", "<->"]:
            return "equiv"
        else:
            return operator

    def set_weights(self):
        misconception_weights = self.calculate_misconception_weights()

        for m, weight in misconception_weights.items():

            misconception = MisconceptionCode.from_string(m)

            associatedOperators = misconception.associatedOperators()
            associatedOperators = [self.operatorToSpot(operator) for operator in associatedOperators]

            for operator in associatedOperators:
                if operator in self.ltl_priorities.keys():

                    ## Geometric scale, perhaps not the right function.
                    ## TODO: Consult about the correct function to change weights here
                    ## This is where ML comes in.
                    
                    self.ltl_priorities[operator] = round(self.ltl_priorities[operator] * ((2 * weight) ** 2))



    def build_exercise(self, literals, complexity, num_questions):

        self.set_weights()

        ## TODO: Find a better mapping between complexity and tree size
        tree_size = complexity

        question_answers = spotutils.gen_rand_ltl(atoms = literals, 
                                                  tree_size = tree_size, 
                                                  ltl_priorities = self.ltl_priorities, 
                                                  num_formulae = num_questions)

        # Generate the exercises
        questions = []
        for answer in question_answers:
            # Generate the exercise
            ltl = ltlnode.parse_ltl_string(answer)
            d = codebook.getAllApplicableMisconceptions(ltl)
            options = []
            for misconception in d:
                options.append({
                    "option": str(misconception.node),
                    "isCorrect": False,
                    "misconceptions": [str(misconception.misconception)]
                })

            # Merge labels for equal formulae
            merged_options = []
            for option in options:
                existing_option = next((o for o in merged_options if o['option'] == option['option']), None)
                if existing_option:
                    existing_option['misconceptions'] += option['misconceptions']
                else:
                    merged_options.append(option)

            if len(merged_options) == 0:
                continue

            # Add the correct answer
            merged_options.append({
                "option": answer,
                "isCorrect": True,
                "misconceptions": []
            })

            questions.append({
                "question": self.gen_nl_question(answer),
                "options": merged_options
            })
        return questions
    
    def gen_nl_question(self, formula):
        ## Oof this is super broken
        formula_eng = ltlnode.parse_ltl_string(formula).__to_english__()
        return f"Which of the following options represent the sentence: '{formula_eng}' ?"

