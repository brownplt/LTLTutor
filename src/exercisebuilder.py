import spotutils
import datetime
from collections import defaultdict
import codebook
from codebook import MisconceptionCode
import ltlnode
import random
import re
import math
import ltltoeng_prose
import ltltoeng_contextualized
from syntacticmutator import applyRandomMutationNotEquivalentTo


class ExerciseBuilder:

    MAX_TRACES = 10
    TRACESATMC = "tracesatisfaction_mc"
    TRACESATYN = "tracesatisfaction_yn"
    ENGLISHTOLTL = "englishtoltl"
    QUESTION_TYPES = [TRACESATMC, TRACESATYN, ENGLISHTOLTL]

    ## No question type's selection probability ever drops below this
    ## (exploration floor), no matter how well the student does on it.
    QUESTION_TYPE_FLOOR = 0.15

    ## A multiple-choice question shows at most this many options total
    ## (1 correct + up to 5 distractors).
    MAX_TOTAL_OPTIONS = 6
    ## Every applicable misconception keeps at least this much sampling weight,
    ## so a resolved/unseen misconception can still surface occasionally and
    ## its weight can be measured back down.
    DISTRACTOR_WEIGHT_FLOOR = 0.25

    COMPLEXITY_MIN = 3
    COMPLEXITY_MAX = 12
    COMPLEXITY_WINDOW = 10
    COMPLEXITY_MIN_ANSWERS = 5
    COMPLEXITY_STEP_UP_ACCURACY = 0.8
    COMPLEXITY_STEP_DOWN_ACCURACY = 0.45


    def __init__(self, userLogs, complexity=5, syntax="Classic"):
        self.userLogs = userLogs
        self.numUserLogs = len(userLogs)

        self.DEFAULT_WEIGHT = 0.7
        self.ltl_priorities = spotutils.DEFAULT_LTL_PRIORITIES.copy()

        ## Persisted per user via the generated_exercise table and updated by
        ## update_complexity(); kept within [COMPLEXITY_MIN, COMPLEXITY_MAX].
        self.complexity = max(self.COMPLEXITY_MIN, min(self.COMPLEXITY_MAX, complexity))

        self.syntax = syntax

        self._distinct_answers_cache = None
        self._question_type_weights_cache = None
        self._misconception_weights_cache = None


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
        """
        Calculate weights for each misconception using an approach inspired by
        Bayesian Knowledge Tracing (BKT) combined with spaced repetition principles.
        
        References:
        - Corbett, A.T. & Anderson, J.R. (1994). Knowledge tracing: Modeling the
          acquisition of procedural knowledge. User Modeling and User-Adapted
          Interaction, 4(4), 253-278. https://doi.org/10.1007/BF01099821
        - Pavlik, P.I. & Anderson, J.R. (2008). Using a model to compute the optimal
          schedule of practice. Journal of Experimental Psychology: Applied, 14(2),
          101-117. https://doi.org/10.1037/1076-898X.14.2.101
        
        The model considers:
        1. Recency: Exponential decay based on spacing effect research (Ebbinghaus)
        2. Frequency: Log-scaled to prevent extreme values from dominating
        3. Trend: Bayesian-style update comparing recent vs historical performance
        4. Drilling: Spaced repetition boost for persistent misconceptions
        """
        weights = {}
        default_weight = 0.5
        
        # BKT-inspired parameters
        # P(L0): Initial probability of having the misconception
        prior_probability = 0.5
        # P(T): Transition probability - likelihood of state change per observation
        # In standard BKT: P(L_n|obs) = P(L_{n-1}) * (1 - P(T)) + (1 - P(L_{n-1})) * P(G)
        # We adapt this for misconceptions where evidence increases belief
        transition_rate = 0.1
        # Decay half-life based on spacing effect research (~24h for short-term)
        recency_half_life_hours = 24
        # Drilling threshold (spaced repetition trigger)
        drilling_threshold = 3
        # Recent window for trend analysis
        recent_window_hours = 48
        # Log scale divisor for frequency normalization
        log_scale_divisor = 3
        # Weight combination factors:
        # BKT weight factor - how much the probabilistic estimate contributes
        bkt_weight_factor = 0.4
        # Frequency weight factor - how much the frequency-based estimate contributes
        frequency_weight_factor = 0.6
        
        # Pre-calculate decay constant: ln(2) / half-life
        decay_constant = -math.log(2) / recency_half_life_hours
        
        now = datetime.datetime.now()
        
        for concept, entries in concept_history.items():
            if not entries:
                weights[concept] = default_weight
                continue
                
            entries.sort()  # Sort by date
            
            # BKT-style sequential update for misconception probability
            p_misconception = prior_probability
            recency_weighted_sum = 0
            recent_count = 0
            total_count = 0
            
            for date, frequency in entries:
                hours_ago = (now - date).total_seconds() / 3600
                
                # Exponential decay factor (Ebbinghaus forgetting curve inspired)
                decay_factor = math.exp(decay_constant * hours_ago)
                recency_weighted_sum += frequency * decay_factor
                total_count += frequency
                
                # Adapted BKT update: evidence of misconception increases belief
                # Standard BKT: P(L_n) = P(L_{n-1}) + (1 - P(L_{n-1})) * P(T)
                # We scale by evidence strength (frequency * recency)
                evidence_strength = min(1.0, frequency * decay_factor)
                p_misconception = p_misconception + (1 - p_misconception) * transition_rate * evidence_strength
                p_misconception = min(0.95, p_misconception)  # Cap to avoid certainty
                
                # Track recent occurrences for drilling
                if hours_ago <= recent_window_hours:
                    recent_count += frequency
            
            # Calculate trend using comparative analysis
            trend_score, _ = self._calculate_trend(entries, now)
            
            # Combine BKT probability with frequency-based weight
            base_weight = math.log1p(recency_weighted_sum) / log_scale_divisor
            
            # Trend adjustment: Bayesian-style evidence weighting
            # Positive trend (worsening) increases weight, negative (improving) decreases
            trend_adjustment = trend_score * 0.2
            
            # Spaced repetition drilling boost for persistent misconceptions
            drilling_boost = 0
            if recent_count >= drilling_threshold:
                # Boost proportional to recent frequency, capped at 0.3
                drilling_boost = min(0.3, recent_count * 0.05)
            
            # Final weight combines BKT probability with frequency-based estimate
            # bkt_weight_factor controls probabilistic contribution
            # frequency_weight_factor controls frequency-based contribution
            weight = (p_misconception * bkt_weight_factor) + (default_weight + base_weight) * frequency_weight_factor
            weight += trend_adjustment + drilling_boost
            
            # Sigmoid squashing to bound output between 0 and 1
            weights[concept] = 1 / (1 + math.exp(-(weight - 0.5)))

        return weights

    def _full_misconception_weights(self):
        """
        Misconception weights over the student's full log history, memoized for
        this builder's lifetime. userLogs is fixed once the builder is created,
        so the weights don't change within a generation pass, and computing them
        is O(#logs). Callers that need weights over a *partial* history (e.g.
        get_model's per-bucket sub-histories) must call
        calculate_misconception_weights directly instead.
        """
        if self._misconception_weights_cache is None:
            self._misconception_weights_cache = self.calculate_misconception_weights(self.aggregateLogs())
        return self._misconception_weights_cache

    def _log_is_correct(self, log):
        """
        Whether a student_responses row records a correct answer.
        correct_answer is stored as a bool in some rows and as the strings
        'True'/'true' in others, so both representations are handled.
        """
        value = getattr(log, 'correct_answer', None)
        if isinstance(value, str):
            return value.lower() == 'true'
        return bool(value)

    def _distinct_answers(self):
        """
        Collapse log rows into one entry per answered question, sorted by time.
        A wrong answer is logged once per misconception on the selected option
        (each row with its own now() timestamp), so raw rows overcount
        incorrect answers.
        """
        if self._distinct_answers_cache is not None:
            return self._distinct_answers_cache

        ordered = sorted(self.userLogs,
                         key=lambda log: getattr(log, 'timestamp', None) or datetime.datetime.min)

        answers = []
        last_kept = {}
        for log in ordered:
            question = getattr(log, 'question_text', None)
            timestamp = getattr(log, 'timestamp', None)
            previous = last_kept.get(question)
            if (previous is not None and timestamp is not None
                    and abs((timestamp - previous).total_seconds()) < 5):
                continue
            last_kept[question] = timestamp
            answers.append(log)

        self._distinct_answers_cache = answers
        return answers

    def calculate_question_type_weights(self):
        """
        Selection weights per question type, biased toward the types the
        student gets wrong. Uses a Laplace-smoothed error rate
        (incorrect + 1) / (attempts + 2), so with no history every type gets
        0.5 and selection is uniform. After normalization, a floor guarantees
        every type keeps at least QUESTION_TYPE_FLOOR probability.
        """
        if self._question_type_weights_cache is not None:
            return self._question_type_weights_cache

        counts = {qtype: {"attempts": 0, "incorrect": 0} for qtype in self.QUESTION_TYPES}
        for answer in self._distinct_answers():
            qtype = getattr(answer, 'question_type', None)
            if qtype not in counts:
                continue
            counts[qtype]["attempts"] += 1
            if not self._log_is_correct(answer):
                counts[qtype]["incorrect"] += 1

        error_rates = {
            qtype: (c["incorrect"] + 1) / (c["attempts"] + 2)
            for qtype, c in counts.items()
        }
        total = sum(error_rates.values())
        normalized = {qtype: rate / total for qtype, rate in error_rates.items()}

        ## Apply the exploration floor: floored types get exactly the floor and
        ## the remaining mass is split proportionally among the rest. Repeat in
        ## case the rescaling pushes another type under the floor.
        result = dict(normalized)
        floored = set()
        for _ in range(len(result)):
            low = {k for k, v in result.items() if k not in floored and v < self.QUESTION_TYPE_FLOOR}
            if not low:
                break
            floored |= low
            free_keys = [k for k in result if k not in floored]
            free_mass = 1.0 - self.QUESTION_TYPE_FLOOR * len(floored)
            free_total = sum(normalized[k] for k in free_keys)
            for k in floored:
                result[k] = self.QUESTION_TYPE_FLOOR
            for k in free_keys:
                if free_total > 0:
                    result[k] = normalized[k] * free_mass / free_total
                else:
                    result[k] = free_mass / len(free_keys)

        self._question_type_weights_cache = result
        return result

    def update_complexity(self):
        """
        Move complexity one step up or down based on the student's recent
        overall accuracy, clamped to [COMPLEXITY_MIN, COMPLEXITY_MAX].
        Requires at least COMPLEXITY_MIN_ANSWERS recent answers to move at all,
        and moves at most one step per call (i.e. per generated exercise).

        This replaces the old always-upward bump that lived inside
        calculate_misconception_weights, whose result was never persisted.
        """
        recent = self._distinct_answers()[-self.COMPLEXITY_WINDOW:]
        if len(recent) >= self.COMPLEXITY_MIN_ANSWERS:
            accuracy = sum(1 for a in recent if self._log_is_correct(a)) / len(recent)
            if accuracy >= self.COMPLEXITY_STEP_UP_ACCURACY:
                self.complexity += 1
            elif accuracy <= self.COMPLEXITY_STEP_DOWN_ACCURACY:
                self.complexity -= 1

        self.complexity = max(self.COMPLEXITY_MIN, min(self.COMPLEXITY_MAX, self.complexity))
        return self.complexity
    
    def _calculate_trend(self, entries, now, window_hours=48):
        """
        Calculate the trend of misconception frequency.
        Returns a tuple (trend_score, has_recent_data) where:
        - trend_score: positive if worsening, negative if improving, 0 if stable
        - has_recent_data: True if there's data within the recent window
        
        If no data is within the recent/older windows, uses relative time-based
        splitting to compare the most recent half of data with the older half.
        """
        if len(entries) < 2:
            # Single entry - new misconception
            if len(entries) == 1:
                return (0.25, True)  # Slight positive to indicate it exists but no trend yet
            return (0, False)
        
        # Sort entries by date (oldest first)
        sorted_entries = sorted(entries, key=lambda x: x[0])
        
        # First, try the absolute time window approach
        recent_sum = 0
        recent_count = 0
        older_sum = 0
        older_count = 0
        
        for date, frequency in sorted_entries:
            hours_ago = (now - date).total_seconds() / 3600
            if hours_ago <= window_hours:
                recent_sum += frequency
                recent_count += 1
            elif hours_ago <= window_hours * 2:
                older_sum += frequency
                older_count += 1
        
        # If we have data in both windows, use absolute time comparison
        if recent_count > 0 and older_count > 0:
            recent_avg = recent_sum / recent_count
            older_avg = older_sum / older_count
            max_avg = max(recent_avg, older_avg)
            if max_avg == 0:
                return (0, True)
            trend = (recent_avg - older_avg) / max_avg
            return (max(-1, min(1, trend)), True)
        
        # If only recent data exists, it's a new or returning misconception
        if recent_count > 0 and older_count == 0:
            return (0.25, True)  # Slight positive - new activity
        
        # No data in recent windows - use relative comparison of all data
        # Split entries into two halves (recent half vs older half)
        mid = len(sorted_entries) // 2
        older_half = sorted_entries[:mid]
        recent_half = sorted_entries[mid:]
        
        older_avg = sum(f for _, f in older_half) / len(older_half)
        recent_avg = sum(f for _, f in recent_half) / len(recent_half)
        
        max_avg = max(recent_avg, older_avg)
        if max_avg == 0:
            return (0, False)
        
        trend = (recent_avg - older_avg) / max_avg
        return (max(-1, min(1, trend)), False)

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

    def generate_template_formulas(self, literals, num_templates=5, weight_threshold=0.5):
        """
        Generate formulas from templates for misconceptions that need specific structural patterns.
        This complements spot's random generation with formulas we know can be mutated.
        Only generates templates for misconceptions where students are struggling (weight > threshold).
        
        Args:
            literals: List of atomic propositions to use in templates
            num_templates: Number of template formulas to generate
            weight_threshold: Only generate templates for misconceptions with weight above this
            
        Returns:
            List of formula strings in spot syntax
        """
        template_formulas = []
        
        # Get misconceptions that need template generation, weighted by their current weights
        misconception_weights = self._full_misconception_weights()
        
        # Filter to only misconceptions that benefit from templates AND have high weight
        template_misconceptions = []
        for m, weight in misconception_weights.items():
            misconception = MisconceptionCode.from_string(m)
            if misconception and misconception.needsTemplateGeneration() and weight > weight_threshold:
                template_misconceptions.append((misconception, weight))
        
        # If no misconceptions are above threshold, don't generate any templates
        if not template_misconceptions:
            return []
        
        # Generate templates, sampling misconceptions by weight
        for _ in range(num_templates):
            # Weighted random choice
            total_weight = sum(w for _, w in template_misconceptions)
            if total_weight == 0:
                continue
                
            r = random.uniform(0, total_weight)
            cumulative = 0
            chosen_misconception = template_misconceptions[0][0]
            
            for misconception, weight in template_misconceptions:
                cumulative += weight
                if r <= cumulative:
                    chosen_misconception = misconception
                    break
            
            # Generate a formula from this misconception's template
            node = chosen_misconception.generateTemplateFormula(atomic_props=literals)
            if node:
                # Convert to spot syntax string
                formula_str = self.toSpotSyntax(str(node))
                template_formulas.append(formula_str)
        
        return template_formulas

    def set_ltl_priorities(self):

        def scale(weight):
            return 2 * weight if weight > 0.5 else 2 * (1 - weight)

        misconception_weights = self._full_misconception_weights()

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
        weights = self.calculate_question_type_weights()
        kinds = list(weights.keys())
        return random.choices(kinds, weights=[weights[k] for k in kinds], k=1)[0]

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
        self.update_complexity()

        ## TODO: Find a better mapping between complexity and tree size
        tree_size = self.get_tree_size()

        ## First generate a large pool from spot randltl
        pool_size = 2*num_questions
        question_answers = spotutils.gen_rand_ltl(atoms = literals,
                                                  tree_size = tree_size,
                                                  ltl_priorities = self.ltl_priorities,
                                                  num_formulae = pool_size)

        ## Augment with template-generated formulas for pattern-specific misconceptions
        ## This helps ensure we get formulas that can actually be mutated with these misconceptions
        template_formulas = self.generate_template_formulas(literals, num_templates=max(1, num_questions // 4))
        question_answers.extend(template_formulas)

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
                # A/B test: 50/50 abstract vs. contextualized framing. The
                # contextualized arm reuses the same formula with literals
                # renamed onto the lights theme, so the two conditions differ
                # only in framing, not in formula structure.
                question = None
                if random.random() < 0.5:
                    ctx_answer = self.gen_contextualized_answer(answer)
                    if ctx_answer is not None:
                        question = self.build_english_to_ltl_question(ctx_answer, contextualized=True)
                if question is None:
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
        result = ltltoeng_prose.translate(as_node)
        if not result or result.strip() == "":
            return None
        return result


    def gen_contextualized_answer(self, formula):
        """Rename *formula*'s literals onto the lights theme.

        Returns the renamed formula string, or None if it cannot be themed
        (parse failure or more distinct literals than the theme has lights).
        """
        try:
            as_node = ltlnode.parse_ltl_string(formula)
        except Exception:
            return None
        remapped = ltltoeng_contextualized.remap_to_theme(as_node)
        return str(remapped) if remapped is not None else None


    def gen_nl_question_contextualized(self, formula):
        """Generate a contextualized English question using the lights theme.

        Expects the formula's literals to already match the theme (see
        gen_contextualized_answer). Returns None if translation fails.
        """
        LIGHTS_THEME = ltltoeng_contextualized.THEMES["lights"]
        as_node = ltlnode.parse_ltl_string(formula)
        result = ltltoeng_contextualized.translate(as_node, LIGHTS_THEME)
        if not result or result.strip() == "":
            return None
        return result


    def _weighted_sample_without_replacement(self, items, weight_fn, k):
        """
        Pick k items from `items` without replacement, with the probability of
        each remaining item proportional to weight_fn(item). Returns fewer than
        k items only if `items` has fewer than k.
        """
        pool = list(items)
        chosen = []
        while pool and len(chosen) < k:
            weights = [max(weight_fn(x), 1e-9) for x in pool]
            total = sum(weights)
            r = random.uniform(0, total)
            upto = 0.0
            picked = len(pool) - 1
            for i, w in enumerate(weights):
                upto += w
                if r <= upto:
                    picked = i
                    break
            chosen.append(pool.pop(picked))
        return chosen

    def _sample_misconception_options(self, options, budget):
        """
        Reduce a list of misconception distractor options to at most `budget`,
        sampling without replacement weighted by misconception weight (with a
        floor so resolved/unseen misconceptions still occasionally appear).
        Returns the list unchanged when it already fits.
        """
        if len(options) <= budget:
            return options

        weights_by_code = self._full_misconception_weights()

        def option_weight(option):
            codes = option.get('misconceptions') or []
            ## An option merged from several misconceptions is weighted by its
            ## most-salient (highest-weight) code.
            raw = max((weights_by_code.get(c, 0.5) for c in codes), default=0.5)
            return self.DISTRACTOR_WEIGHT_FLOOR + raw

        return self._weighted_sample_without_replacement(options, option_weight, budget)

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

        correct_option = {
            "option": self.getLTLFormulaAsString(ltl),
            "isCorrect": True,
            "misconceptions": []
        }

        ### BUILD A SINGLE RANDOM SYNTACTIC MUTATION (the red-herring control)
        ## THAT IS NOT EQUIVALENT TO THE CORRECT ANSWER OR ANY OTHER OPTION
        notEquivalentToNodes = [ltlnode.parse_ltl_string(o['option']) for o in merged_options]
        notEquivalentToNodes.append(ltl)
        mutated_node = applyRandomMutationNotEquivalentTo(ltl, notEquivalentToNodes)
        syntactic_option = None
        if mutated_node is not None:
            syntactic_option = {
                "option": self.getLTLFormulaAsString(mutated_node),
                "isCorrect": False,
                "misconceptions": [str(MisconceptionCode.Syntactic)]
            }

        ## Cap the total number of options. Reserve one wrong slot for the
        ## syntactic control when present, and fill the rest with misconception
        ## distractors sampled by weight (mastered misconceptions fade out).
        wrong_budget = self.MAX_TOTAL_OPTIONS - 1
        misconception_budget = wrong_budget - (1 if syntactic_option is not None else 0)
        sampled = self._sample_misconception_options(merged_options, misconception_budget)

        final_options = list(sampled)
        if syntactic_option is not None:
            final_options.append(syntactic_option)
        final_options.append(correct_option)

        return final_options

    def build_english_to_ltl_question(self, answer, contextualized=False):

        options = self.get_options_with_misconceptions_as_formula(answer)
        if options is None:
            return None

        if contextualized:
            question = self.gen_nl_question_contextualized(answer)
            translation_mode = "contextualized"
            # Fall back to abstract if contextualized translation fails
            if question is None or question == "":
                question = self.gen_nl_question(answer)
                translation_mode = "abstract"
        else:
            question = self.gen_nl_question(answer)
            translation_mode = "abstract"

        if question is None or question == "":
            print("Question generation failed unexpectedly.")
            return None

        return {
            "question": question,
            "type": self.ENGLISHTOLTL,
            "options": options,
            "translation_mode": translation_mode
        }

    def build_tracesat_mc_question(self, answer):
        import exerciseprocessor

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
                potential_trace_choices = [exerciseprocessor.canonicalizeSpotTrace(t) for t in potential_trace_choices]
                potential_trace_choices = list(dict.fromkeys(potential_trace_choices))
                existing_trace_options = [option['option'] for option in trace_options]
                trace_choices = [t for t in potential_trace_choices if t not in existing_trace_options]
                attempt_number += 1

            if len(trace_choices) == 0:
                ## Maybe TODO: We should generate a random traces here that accepts true?
                continue

            trace_options.append( {
                'option': spotutils.weighted_trace_choice(trace_choices),
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
        import exerciseprocessor

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

        potential_trace_choices = [exerciseprocessor.canonicalizeSpotTrace(t) for t in potential_trace_choices]
        potential_trace_choices = list(dict.fromkeys(potential_trace_choices))
        
        if len(potential_trace_choices) == 0:
            return None
        
        # Use weighted selection to slightly prefer shorter traces
        trace_option = spotutils.weighted_trace_choice(potential_trace_choices)

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
        misconception_trends = {}

        ## Buckets is a dictionary where keys are misconceptions and values are lists of tuples (timestamp, frequency) 
        misconception_weights = self.calculate_misconception_weights(concept_history)
        misconception_count = 0

        now = datetime.datetime.now()

        for misconception in concept_history:


            buckets_for_misconception = concept_history[misconception]



            ## Sort the buckets by date
            buckets_for_misconception.sort(key=lambda x: x[0])
            n = len(buckets_for_misconception)

            # Calculate trend for this misconception
            trend_score, has_recent_data = self._calculate_trend(buckets_for_misconception, now)
            trend_label = self._get_trend_label(trend_score)
            misconception_trends[misconception] = {
                "score": trend_score,
                "label": trend_label,
                "has_recent_data": has_recent_data
            }

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
            "misconception_trends": misconception_trends,
            "complexity": self.complexity,
            'misconception_count': misconception_count
        }

    def _complexity_band(self):
        """Coarse label for the current complexity within [MIN, MAX]:
        lowest third Beginner, middle third Intermediate, top third Advanced."""
        span = self.COMPLEXITY_MAX - self.COMPLEXITY_MIN
        if span <= 0:
            return "Intermediate"
        position = (self.complexity - self.COMPLEXITY_MIN) / span
        if position < 1 / 3:
            return "Beginner"
        if position < 2 / 3:
            return "Intermediate"
        return "Advanced"

    def get_profile_snapshot(self):
        """A point-in-time view of the state the exercise engine uses to adapt,
        for display on the student profile page and the JSON export:

          - complexity: the current difficulty level and its band, plus bounds
          - misconception_snapshot: per-misconception weights the distractor
            sampler uses now (the enum prefix stripped), most-likely first
          - question_type_weights: the selection weights per question type

        Pure w.r.t. the builder's logs (no SPOT, no DB), so it is safe to call
        from a request handler and straightforward to unit-test."""
        weights = self._full_misconception_weights()
        misconception_snapshot = [
            {"name": code.replace('MisconceptionCode.', ''), "weight": weight}
            for code, weight in sorted(weights.items(),
                                       key=lambda kv: kv[1], reverse=True)
        ]

        return {
            "complexity": self.complexity,
            "complexity_min": self.COMPLEXITY_MIN,
            "complexity_max": self.COMPLEXITY_MAX,
            "complexity_band": self._complexity_band(),
            "misconception_snapshot": misconception_snapshot,
            "question_type_weights": self.calculate_question_type_weights(),
        }

    def _get_trend_label(self, trend_score):
        """
        Convert a trend score (-1 to 1) to a human-readable label.
        """
        if trend_score <= -0.5:
            return "Improving significantly"
        elif trend_score <= -0.2:
            return "Improving"
        elif trend_score < 0.2:
            return "Stable"
        elif trend_score < 0.5:
            return "Needs attention"
        else:
            return "Needs focus"
