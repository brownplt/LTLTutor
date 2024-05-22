import spotutils
import datetime
from collections import defaultdict
import codebook
from codebook import MisconceptionCode
import ltlnode
import random
import re
import math

class ExerciseBuilder:

    MAX_TRACES = 10
    TRACESATMC = "tracesatisfaction_mc"
    TRACESATYN = "tracesatisfaction_yn"
    ENGLISHTOLTL = "englishtoltl"

    def __init__(self, userLogs, complexity=5):
        self.userLogs = userLogs
        self.DEFAULT_WEIGHT = 0.7
        self.ltl_priorities = spotutils.DEFAULT_LTL_PRIORITIES.copy()

        ## TODO: We want complexity to be persistent for user, and scale up or down.
        self.complexity = complexity
   
    


    def aggregateLogs(self, bucketsizeinhours=1):

        concept_history = defaultdict(list)

        # Create an empty dictionary to store the buckets
        buckets = defaultdict(lambda: defaultdict(int))

        # Iterate over the log entries
        for log in self.userLogs:
            timestamp = log.timestamp
            # Calculate the bucket for the log entry
            bucket = timestamp.replace(minute=0, second=0, microsecond=0)
            bucket += datetime.timedelta(hours=(timestamp.hour % bucketsizeinhours))

            # Add the log entry to the corresponding bucket
            misconception = log.misconception
            buckets[bucket][misconception] += 1

        # Organize misconceptions by bucket and sort by date
        for bucket, misconceptions in buckets.items():
            for misconception, frequency in misconceptions.items():
                concept_history[misconception].append((bucket, frequency))
        

        # For all concepts, add them at 0 frequency to all buckets where they are missing

        # I want a list of all MisconceptionCode from enum MisconceptionCode
        all_misconceptions = [str(m) for m in MisconceptionCode]

        for misconception in all_misconceptions:
            if misconception not in concept_history:
                concept_history[misconception] = []
        return concept_history


   
    def calculate_misconception_weights(self):
        concept_history = self.aggregateLogs()
        weights = {}
        default_weight = 0.5  # This is a parameter you can adjust

        for concept, entries in concept_history.items():
            entries.sort()  # Sort by date
            weight = default_weight
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

            # Apply sigmoid function to scale weight between 0 and 1 (adjusted for default weight by 0.5)
            weights[concept] = 1 / (1 + math.exp(-(weight - 0.5)))

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

    def set_ltl_priorities(self):

        def scale(weight):
            return 2 * weight if weight > 0.5 else 2 * (1 - weight)

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
                    
                    oldval = self.ltl_priorities[operator]
                    newval = round(self.ltl_priorities[operator] * scale(weight))
                    self.ltl_priorities[operator] = newval

            #print("Priotities now are " + str(self.ltl_priorities))


    def choose_question_kind(self):
        ## TODO: Maybe this can be more sophisticated, looking at the kinds of questions students
        ## have gotten wrong in the past
        return random.choice([self.TRACESATMC, self.ENGLISHTOLTL, self.TRACESATYN])

    def get_tree_size(self):
        ## TODO: Determine complexity somehow, maybe based on the number of misconceptions encountered
        ## and then create a mapping to tree size

        ## Complexity, perhaps can be a combination of tree size
        ## Expression heirarchy? Number of literals?
        ## Mana Pneuli class? Maybe we need something else here?
        return self.complexity

    def build_exercise(self, literals, num_questions):

        TAUTOLOGY = "1"
        UNSAT = "0"
        def contains_unsat(s):
            return bool(re.search(r'\b0\b', s))
        def contains_tautology(s):
            return bool(re.search(r'\b0\b', s))
     

        self.set_ltl_priorities()

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

            ## Lets make this even more conservative.
            ## If the answer contains UNSAT or a tautology, skip it.
            if contains_tautology(answer) or contains_unsat(answer):
                continue

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
        #print("Generating NL question for " + formula + " and got " + str(formula_eng))

        ### If there are multiple '.' in a row, replace with a single '.'
        formula_eng = re.sub(r'\.{2,}', '.', formula_eng)
        
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
                'misconceptions': misconceptions,
                'generatedFromFormula': formula
            })
    

        if len(trace_options) < 2:
            return None

        return {
            "question": parenthesized_answer,
            "type": self.TRACESATMC,
            "options": trace_options,
        }

    def build_tracesat_yn_question(self, answer):
        formulae = self.get_options_with_misconceptions_as_formula(answer)
        parenthesized_answer = str(ltlnode.parse_ltl_string(answer))
        


        feedbackString = "No further feedback is currently available. An update is planned, providing feedback in terms of an 'Trace Stepper' that will allow you to step through the trace and see where/if it diverges from the formula."
        # So no misconceptions forthcoming...
        ## TODO: Should we even generate a question one here?
        if formulae is None:
            ## Generate a trace to accept the formula
            potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            misconceptions = []
            yesIsCorrect = True
        else:
            ## Choose a random option
            formula = random.choice(formulae)
            yesIsCorrect = formula['isCorrect']
            formula_asString = formula['option']
            if yesIsCorrect: 
                potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            else:
                potential_trace_choices = spotutils.generate_traces(f_accepted=formula_asString, f_rejected=parenthesized_answer)
                feedbackString = f"The trace is accepted by the formula <code>{formula_asString}</code>, but not by the formula <code>{parenthesized_answer}</code>."
            misconceptions = formula['misconceptions']
        
        if len(potential_trace_choices) == 0:
            return None
        
        trace_option = random.choice(potential_trace_choices)

        ## THink about this -- how can we give feedback here!
        yes_misconceptions = [] if yesIsCorrect else misconceptions
        no_misconceptions = misconceptions if yesIsCorrect else []

        options = [

            {
              'option': 'Yes',
              'isCorrect': yesIsCorrect,
               'misconceptions': yes_misconceptions
             },
            {
              'option': 'No',
              'isCorrect': not yesIsCorrect,
              'misconceptions': no_misconceptions
            }

        ]

        return {
            "question": parenthesized_answer,
            "trace": trace_option,
            "type": self.TRACESATYN,
            "options": options,
            'feedback': feedbackString
        }
        

    def get_model(self):

        buckets = self.aggregateLogs()
        # I want to add all the values of the buckets to get a count
        misconception_count = 0
        for misconception in buckets:
            buckets_for_misconception = buckets[misconception]
            # concept_history[misconception].append((bucket, frequency))
            for bucket, frequency in buckets_for_misconception:
                misconception_count += frequency

        misconception_weights = self.calculate_misconception_weights()
        return {
            "misconception_weights": misconception_weights,
            "misconceptions_over_time": buckets,
            "complexity": self.complexity,
            'misconception_count': misconception_count
        }