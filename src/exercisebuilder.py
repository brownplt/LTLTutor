import spotutils
import datetime
from collections import defaultdict
import codebook
from codebook import MisconceptionCode
import ltlnode
import random
import re
import math
import ltltoeng
from syntacticmutator import applyRandomMutationNotEquivalentTo


class ExerciseBuilder:

    MAX_TRACES = 10
    TRACESATMC = "tracesatisfaction_mc"
    TRACESATYN = "tracesatisfaction_yn"
    ENGLISHTOLTL = "englishtoltl"


    def __init__(self, userLogs, complexity=5, syntax="Classic"):
        self.userLogs = userLogs
        self.numUserLogs = len(userLogs)

        self.DEFAULT_WEIGHT = 0.7
        self.ltl_priorities = spotutils.DEFAULT_LTL_PRIORITIES.copy()

        ## TODO: We want complexity to be persistent for user, and scale up or down.
        self.complexity = complexity
   
        self.syntax = syntax


    def toSpotSyntax(self, s):
        return str(ltlnode.parse_ltl_string(s))
    


    def getLTLFormulaAsString(self, node):


        ## Check if node is a string ##
        if isinstance(node, str):
            node = ltlnode.parse_ltl_string(node)


        if self.syntax == "Classic":
            return str(node)
        elif self.syntax == "Forge":
            return node.__forge__()
        elif self.syntax == "Electrum":
            return node.__electrum__()
        elif self.syntax == "English":
            ## We should hopefully never get here. However, 
            ## I'm adding it here to suggest a way forward.
            return node.__to_english__()

        ## Default to classic syntax
        return str(node)


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

        # Make sure we are not adding any misconceptions that are not in the codebook
        to_return = { k : v for k, v in concept_history.items() if k in all_misconceptions}

        return to_return


   
    def calculate_misconception_weights(self, concept_history):

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

        if max(weights.values()) < default_weight:
            print("Increasing complexity for user")
            self.complexity += 1
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

        concept_history = self.aggregateLogs()
        misconception_weights = self.calculate_misconception_weights(concept_history)

        for m, weight in misconception_weights.items():

            misconception = MisconceptionCode.from_string(m)

            if misconception is None:
                continue

            associatedOperators = misconception.associatedOperators()
            associatedOperators = [self.operatorToSpot(operator) for operator in associatedOperators]



            for operator in associatedOperators:

                if operator in self.ltl_priorities.keys():

                    ## Geometric scale, perhaps not the right function.
                    ## TODO: Consult about the correct function to change weights here
                    ## This is where ML comes in.
                    
                    oldval = self.ltl_priorities[operator]
                    newval = round(oldval * scale(weight))
                    self.ltl_priorities[operator] = newval


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

        def contains_undersirable_lit(s):
            TAUTOLOGY = r'\b1\b'
            UNSAT = r'\b0\b'
            # remove all the parens
            y = s.replace('(', ' ').replace(')', ' ').replace("'", ' ')
            x = bool(re.search(TAUTOLOGY, y)) or bool(re.search(UNSAT, y))

            return x


        self.set_ltl_priorities()

        ## TODO: Find a better mapping between complexity and tree size
        tree_size = self.get_tree_size()

        ## First generate a large pool
        pool_size = 2*num_questions
        question_answers = spotutils.gen_rand_ltl(atoms = literals, 
                                                  tree_size = tree_size, 
                                                  ltl_priorities = self.ltl_priorities, 
                                                  num_formulae = pool_size)
        

        def formula_choice_metric(formula):

            temporal_op_count = formula.count('G') + formula.count('X') + formula.count('U') + formula.count('F')
            aut_size = spotutils.get_aut_size(formula)


            scaled_aut_size = aut_size * math.log(self.numUserLogs + 1)
            return temporal_op_count + scaled_aut_size


        # Generate the exercises
        questions = []
        for answer in question_answers:

            ## Lets make this even more conservative.
            ## If the answer contains UNSAT or a tautology, skip it.
            if contains_undersirable_lit(answer):
                continue


            kind = self.choose_question_kind()

            if kind == self.TRACESATMC:
                question = self.build_tracesat_mc_question(answer)
            elif kind == self.ENGLISHTOLTL:
                question = self.build_english_to_ltl_question(answer)
            elif kind == self.TRACESATYN:
                question = self.build_tracesat_yn_question(answer)

            if question is not None:
                question['score'] = formula_choice_metric(answer)
                questions.append(question)



        # sort questions by score
        chosen_questions = sorted(questions, key=lambda x: x['score'], reverse=True)

        # Now choose the question with the highest metric, that is of each type from the chosen_questions
        highest_ltl_to_eng = next((q for q in chosen_questions if q['type'] == self.ENGLISHTOLTL), None)
        highest_trace_sat_mc = next((q for q in chosen_questions if q['type'] == self.TRACESATMC), None)
        highest_trace_sat_yn = next((q for q in chosen_questions if q['type'] == self.TRACESATYN), None)


        final_choices = []
        if highest_ltl_to_eng is not None:
            final_choices.append(highest_ltl_to_eng)
        if highest_trace_sat_mc is not None:
            final_choices.append(highest_trace_sat_mc)
        if highest_trace_sat_yn is not None:
            final_choices.append(highest_trace_sat_yn)

        remaining = num_questions - len(final_choices)
        if remaining > 0:
            # Add the remaining questions from chosen_questions, but dont add the ones already added
            for q in chosen_questions:
                if q not in final_choices:
                    final_choices.append(q)
                    remaining -= 1
                if remaining <= 0:
                    break

                    

        return final_choices

    
    def gen_nl_question(self, formula):

        as_node = ltlnode.parse_ltl_string(formula)
        formula_eng = as_node.__to_english__()
        if formula_eng is None or formula_eng == "":
            return None
        
        formula_eng_corrected = ltltoeng.correct_grammar(formula_eng)
        ### If there are multiple '.' in a row, replace with a single '.'
        formula_eng_corrected = re.sub(r'\.{2,}', '.', formula_eng)
        return formula_eng_corrected


    def get_options_with_misconceptions_as_formula(self, answer):
        ltl = ltlnode.parse_ltl_string(answer)
        d = codebook.getAllApplicableMisconceptions(ltl)

        options = []
        for misconception in d:
            options.append({
                "option": self.getLTLFormulaAsString(misconception.node),
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
                "option": self.getLTLFormulaAsString(ltl),
                "isCorrect": True,
                "misconceptions": []
            })
        

        ### NOW, ADD A SINGLE RANDOM SYNTACTIC MUTATION
        ## THAT IS NOT EQUIVALENT TO THE CORRECT ANSWER
        ## OR ANY OF THE OTHER OPTIONS
        notEquivalentToNodes = [ltlnode.parse_ltl_string(o['option']) for o in merged_options]
        mutated_node = applyRandomMutationNotEquivalentTo(ltl, notEquivalentToNodes)
        if mutated_node is not None:
            merged_options.append({
                "option": self.getLTLFormulaAsString(mutated_node),
                "isCorrect": False,
                "misconceptions": [str(MisconceptionCode.Syntactic)]
            })
        

        return merged_options

    def build_english_to_ltl_question(self, answer):
        
        options = self.get_options_with_misconceptions_as_formula(answer)
        if options is None:
            return None

        question = self.gen_nl_question(answer)

        if question is None or question == "":
            print("Question generation failed unexpectedly.")
            return None

        return {
            "question": question,
            "type": self.ENGLISHTOLTL,
            "options": options
        }

    def build_tracesat_mc_question(self, answer):
        options = self.get_options_with_misconceptions_as_formula(answer)
        if options is None:
            return None
        
        parenthesized_answer = self.toSpotSyntax(answer)
        
        trace_options = []
        for o in options:
            formula = self.toSpotSyntax(o['option'])
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
                'generatedFromFormula': self.getLTLFormulaAsString(formula) ## Should this be the formula we want?
            })
    

        if len(trace_options) < 2:
            return None

        answer_in_correct_syntax = self.getLTLFormulaAsString(ltlnode.parse_ltl_string(answer))

        return {
            "question": answer_in_correct_syntax,
            "type": self.TRACESATMC,
            "options": trace_options,
        }

    def build_tracesat_yn_question(self, answer):
        formulae = self.get_options_with_misconceptions_as_formula(answer)
        parenthesized_answer = self.toSpotSyntax(answer)
    

        feedbackString = "No further feedback is currently available. We recommend stepping through the trace to see where/if it diverges from the formula."
        # So no misconceptions forthcoming...
        ## TODO: Should we even generate a question one here?
        if formulae is None:
            ## Generate a trace to accept the formula
            # potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            # misconceptions = []
            # yesIsCorrect = True
            print("Skipping generation of traceSAT Y/N Question for formula: ", parenthesized_answer, " as no candidate misconceptions were found.")
            ### We can't get a potential misconception here, so we skip generation here.
            return None
        else:
            ## Choose a random option
            formula = random.choice(formulae)
            yesIsCorrect = formula['isCorrect']
            formula_asString = self.toSpotSyntax(formula['option'])
            if yesIsCorrect: 
                potential_trace_choices = spotutils.generate_accepted_traces(parenthesized_answer)
            else:
                potential_trace_choices = spotutils.generate_traces(f_accepted=formula_asString, f_rejected=parenthesized_answer)


                ## LTL Formula to Show
                option_in_correct_syntax = self.getLTLFormulaAsString(formula_asString)
                correct_option_in_correct_syntax  = self.getLTLFormulaAsString(parenthesized_answer)


                feedbackString = f"The trace is accepted by the formula <code>{option_in_correct_syntax}</code>, but not by the formula <code>{correct_option_in_correct_syntax}</code>."
            misconceptions = formula['misconceptions']
        
        if len(potential_trace_choices) == 0:
            return None
        
        # TODO: Should this be expanded?
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
        answer_in_correct_syntax = self.getLTLFormulaAsString(ltlnode.parse_ltl_string(answer))
        return {
            "question": answer_in_correct_syntax,
            "trace": trace_option,
            "type": self.TRACESATYN,
            "options": options,
            'feedback': feedbackString
        }
        

    def get_model(self):

        concept_history = self.aggregateLogs()
        misconception_weights_over_time = { k : [] for k in concept_history.keys()}
        misconception_weights = {}

        ## Buckets is a dictionary where keys are misconceptions and values are lists of tuples (timestamp, frequency) 
        misconception_weights = self.calculate_misconception_weights(concept_history)
        misconception_count = 0

        

        for misconception in concept_history:


            buckets_for_misconception = concept_history[misconception]



            ## Sort the buckets by date
            buckets_for_misconception.sort(key=lambda x: x[0])
            n = len(buckets_for_misconception)

            for i in range(n):
                time_bucket, frequency = buckets_for_misconception[i]
                misconception_count += frequency

                sub_history = { misconception : buckets_for_misconception[:i+1]}



                weight = self.calculate_misconception_weights(sub_history)
                to_append = {
                    "time" :time_bucket, 
                    "weight": weight[misconception]
                }

                
                #to_append = (time_bucket, weight[misconception])
                misconception_weights_over_time[misconception].append(to_append)

        return {
            "misconception_weights": misconception_weights,
            "misconception_weights_over_time": misconception_weights_over_time,
            "complexity": self.complexity,
            'misconception_count': misconception_count
        }