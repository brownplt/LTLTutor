import spotutils
import datetime
from collections import defaultdict
import codebook
from codebook import MisconceptionCode
import ltlnode
import random
import string

## TODO
# Normalize LTL priorities


class ExerciseBuilder:

    MAX_TRACES = 10

    TRACESATMC = "tracesatisfaction_mc"
    TRACESATYN = "tracesatisfaction_yn"
    ENGLISHTOLTL = "englishtoltl"

    def __init__(self, userLogs):
        self.userLogs = userLogs
        self.DEFAULT_WEIGHT = 0.7
        self.ltl_priorities = spotutils.DEFAULT_LTL_PRIORITIES.copy()
        self.complexity = 5
   
    
    def normalize_ltl_priorities(self):
        temporal_operators = ["X", "F", "G", "U"]
        #to_consider = [op for op in self.ltl_priorities.keys() if op in temporal_operators]
        # Normalize the weights of keys in temporal_operators, in the range of 0 to 10
        xs =[ self.ltl_priorities[op] for op in temporal_operators]

        
        max_weight = max(xs)
        max_weight = max(1, max_weight)

        if max_weight < spotutils.DEFAULT_WEIGHT:
            ## Increase base complexity
            # TODO: This is not great, since we haven't logged previous complexity.
            self.complexity += 2

        for op in temporal_operators:
            self.ltl_priorities[op] = round(self.ltl_priorities[op] * 9 / max_weight) + 1

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

            weights[concept] = max(weight, 1)  # Ensure weights don't go negative

        ## Why is weights empty ever?

        ## TODO: Do we want this normalization, given we normalize the LTL priorities?
        # max_weight = max(weights.values())
        # for concept in weights:
        #     weights[concept] /= max_weight

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
            ## TODO: Do we want this normalization?
            self.normalize_ltl_priorities()


    def choose_question_kind(self):
        ## TODO: Maybe this can be more sophisticated, looking at the kinds of questions students
        ## have gotten wrong in the past
        return random.choice([self.TRACESATMC, self.ENGLISHTOLTL, self.TRACESATYN])

    def get_tree_size(self):
        ## TODO: Determine complexity somehow, maybe based on the number of misconceptions encountered
        ## and then create a mapping to tree size
        return self.complexity

    def build_exercise(self, literals, num_questions):

        self.set_weights()

        ## TODO: Find a better mapping between complexity and tree size
        tree_size = self.get_tree_size()

        ## First generate a large pool
        pool_size = 2*num_questions
        question_answers = spotutils.gen_rand_ltl(atoms = literals, 
                                                  tree_size = tree_size, 
                                                  ltl_priorities = self.ltl_priorities, 
                                                  num_formulae = pool_size)
        # Generate the exercises
        questions = []
        for answer in question_answers:
            kind = self.choose_question_kind()

            if kind == self.TRACESATMC:
                question = self.build_tracesat_mc_question(answer)
            elif kind == self.ENGLISHTOLTL:
                question = self.build_english_to_ltl_question(answer)
            elif kind == self.TRACESATYN:
                question = self.build_tracesat_yn_question(answer)

            if question is not None:
                questions.append(question)

        ## Make sure we have enough questions
        chosen_questions = random.sample(questions, min(num_questions, len(questions)))
        return chosen_questions
    
    def gen_nl_question(self, formula):
        formula_eng = ltlnode.parse_ltl_string(formula).__to_english__()
        return formula_eng


    def get_options_with_misconceptions_as_formula(self, answer):
        ltl = ltlnode.parse_ltl_string(answer)
        d = codebook.getAllApplicableMisconceptions(ltl)

        options = []
        for misconception in d:
            options.append({
                "option": str(misconception.node),
                "isCorrect": False,
                "misconceptions": [str(misconception.misconception)]
            })
        merged_options = []
        for option in options:
            existing_option = next((o for o in merged_options if o['option'] == option['option']), None)
            if existing_option:
                existing_option['misconceptions'] += option['misconceptions']
            else:
                merged_options.append(option)

        ## If we couldn't build anything here, skip it
        if len(merged_options) == 0:
            return None
        
        merged_options.append({
                "option": str(ltl),
                "isCorrect": True,
                "misconceptions": []
            })
        return merged_options

    def build_english_to_ltl_question(self, answer):
        
        options = self.get_options_with_misconceptions_as_formula(answer)
        if options is None:
            return None

        return {
            "question": self.gen_nl_question(answer),
            "type": self.ENGLISHTOLTL,
            "options": options
        }



    def build_tracesat_mc_question(self, answer):
        options = self.get_options_with_misconceptions_as_formula(answer)
        if options is None:
            return None
        
        parenthesized_answer = str(ltlnode.parse_ltl_string(answer))
        
        trace_options = []
        for o in options:
            formula = o['option']
            isCorrect = o['isCorrect']
            misconceptions = o['misconceptions']


            max_trace_gen_attempts = 3
            attempt_number = 1
            trace_choices = []

            while (len(trace_choices) == 0) and (attempt_number <= max_trace_gen_attempts):
                max_choice_size = attempt_number * self.MAX_TRACES
                if isCorrect: 
                    potential_trace_choices = spotutils.generate_accepted_traces(formula, max_traces=max_choice_size)
                else:
                    potential_trace_choices = spotutils.generate_traces(f_accepted=formula, f_rejected=parenthesized_answer, max_traces=max_choice_size)
                existing_trace_options = [option['option'] for option in trace_options]
                trace_choices = [t for t in potential_trace_choices if t not in existing_trace_options]
                attempt_number += 1

            if len(trace_choices) == 0:
                ## Maybe TODO: We should generate a random traces here that accepts true?
                continue

            trace_options.append( {
                'option': random.choice(trace_choices),
                'isCorrect': isCorrect,
                'misconceptions': misconceptions
            })
    

        if len(trace_options) < 2:
            return None

        return {
            "question": parenthesized_answer,
            "type": self.TRACESATMC,
            "options": trace_options
        }




    def build_tracesat_yn_question(self, answer):
        formulae = self.get_options_with_misconceptions_as_formula(answer)
        parenthesized_answer = str(ltlnode.parse_ltl_string(answer))
        
        if formulae is None:
            ## Generate a trace to accept the formula
            potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            misconceptions = []
        else:
            ## Choose a random option
            formula = random.choice(formulae)
            isCorrect = formula['isCorrect']
            if isCorrect: 
                potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            else:
                potential_trace_choices = spotutils.generate_traces(f_accepted=formula, f_rejected=parenthesized_answer)
            misconceptions = formula['misconceptions']
        
        if len(potential_trace_choices) == 0:
            return None
        
        trace_option = random.choice(potential_trace_choices)

        ## THink about this
        yes_misconceptions = [] if isCorrect else misconceptions
        no_misconceptions = misconceptions if isCorrect else []
        options = [

            {
              'option': 'Yes',
              'isCorrect': isCorrect,
               'misconceptions': yes_misconceptions
             },
            {
              'option': 'No',
              'isCorrect': not isCorrect,
              'misconceptions': no_misconceptions
            }

        ]

        ## TODO: This needs to be fixed, trace_option needs tobe found.
        return {
            "question": parenthesized_answer,
            "trace": trace_option,
            "type": self.TRACESATYN,
            "options": options
        }
        
