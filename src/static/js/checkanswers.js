function getExerciseName() {
    let en = document.getElementById('exerciseName');
    if (en && en.innerText != "") {
        return en.innerText;
    }
    console.error("Could not find exercise name.");
    return "Unknown Exercise";
}

function getQuestionText(parentNode) {
    return parentNode.querySelector('.actualQuestion').innerText;
}

function getQuestionTrace(parentNode) {
    return parentNode.querySelector('.actualQuestionTrace').innerText;
}

function getQuestionOptions(parentNode) {

    let allRadios = parentNode.querySelectorAll('input[type=radio]');
    return Array.from(allRadios).map(r => ({
        value: r.value,
        misconceptions: r.dataset.misconceptions
    }));
}


function getSelectedRadio(parentNode) {
    let selectedRadio =  parentNode.querySelector('input[type=radio]:checked');
    if (selectedRadio == null) {
        alert("Please select an option");
    }
    return selectedRadio;
}
function getCorrectRadio(parent_node) {
    var correct_option = parent_node.querySelector('input[data-correct="True"]');
    return correct_option;
}


function getGeneratedFromFormulaIfExists(radioButton) {

    let formula = radioButton.dataset.generatedfromformula;
    if (formula) {
        return formula;
    }
    return null;
}

// Prevent users from changing their answer after seeing feedback
function lockQuestionInteractions(parent_node) {
    let radios = parent_node.querySelectorAll('input[type=radio]');
    Array.from(radios).forEach(radio => {
        radio.disabled = true;
    });

    let checkButton = parent_node.querySelector('.checkanswer');
    if (checkButton) {
        checkButton.disabled = true;
    }
}


function show_feedback(parent_node, question_type) {

    let all_radios = parent_node.querySelectorAll('input[type=radio]');
    Array.from(all_radios).forEach(radio => {
        //radio.parentNode.style.outline = "none";
        radio.parentNode.parentNode.classList.remove("bg-success");
        radio.parentNode.parentNode.classList.remove("bg-danger");
    });
    let selected_radio = getSelectedRadio(parent_node);

    if (selected_radio == null) {
        return false;
    }





    let selected_option = selected_radio.value;
    let correct_radio = getCorrectRadio(parent_node);
    let correct_option = correct_radio.value;
    let feedback_div = document.querySelector('#feedback');
    let correct = selected_option == correct_option;

    if (correct) {
        // Make the background of the selected radio button green
        // selected_option.parentNode.style.backgroundColor = "lightgreen";

        // selected_radio.parentNode.style.outline = "2px solid green";

        selected_radio.parentNode.parentNode.classList.add("bg-success");

        

        // Add a message to the feedback div
        feedback_div.innerHTML = "<p> Correct answer! 🎉🥳 Great job! </p>";
        feedback_div.classList.add('alert');
        feedback_div.classList.add('alert-success');
        feedback_div.classList.remove('alert-secondary');

        try {
            // Increment the correct count
            let correctCountElement = document.getElementById('correctCount');
            let currentCount = parseInt(correctCountElement.innerText);
            correctCountElement.innerText = currentCount + 1;
        }
        catch (error) {
            console.err("Something went wrong. Could not increment correctness count.");
        }
    }
    else {

        function getStepperFormHtml(formula, trace, label) {
            return `
                    <form action="/stepper" method="post" target="_blank" class="d-inline-block mr-2 mt-1">
                        <input type="hidden" name="formula" value='${formula}'>
                        <input type="hidden" name="trace" value='${trace}'>
                        <button type="submit" class="btn btn-secondary">${label}</button>
                    </form>
                    `;
        }

        function getTraceStepperButtonHtml() {
            var formulaForStepper = get_formula_for_MP_Classification(parent_node, question_type);
            if (question_type == "trace_satisfaction_yn") {
                return getStepperFormHtml(formulaForStepper, getQuestionTrace(parent_node).trim(),
                    "Step through this trace and the formula.");
            }
            if (question_type == "trace_satisfaction_mc") {
                // The selected trace violates the question formula; the correct
                // trace satisfies it. Offer both pairings, clearly labeled.
                return getStepperFormHtml(formulaForStepper, getSelectedRadio(parent_node).value.trim(),
                        "See why your trace fails the formula.")
                    + getStepperFormHtml(formulaForStepper, getCorrectRadio(parent_node).value.trim(),
                        "See why the correct trace satisfies the formula.");
            }
            return "";
        }



        correct_radio.parentNode.parentNode.classList.add("bg-success");
        selected_radio.parentNode.parentNode.classList.add("bg-danger");

        misconception_string = selected_radio.dataset.misconceptions.replace(/'/g, '"');
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is highlighted in green (i.e: <code>" + correct_option + "</code> )</p>" + getTraceStepperButtonHtml();
        feedback_div.classList.add('alert');
        feedback_div.classList.remove('alert-success');
        feedback_div.classList.add('alert-secondary');


        // Check if parent_node has a child of class 'predeterminedfeedback'
        let predetermined_feedback = parent_node.querySelector('.predeterminedfeedback');

        let selectedAnswerFormula = getGeneratedFromFormulaIfExists(selected_radio);
        let correctAnswerFormula = getGeneratedFromFormulaIfExists(correct_radio);


        if (predetermined_feedback) {
            predetermined_feedback = predetermined_feedback.innerHTML;
            feedback_div.innerHTML += "<p>" + predetermined_feedback + "</p>";
        }
        if (selectedAnswerFormula && correctAnswerFormula) {
            feedback_div.innerHTML += "<p> Hint: The option you selected satisfies : <pre class='language-ltl'><code>" + selectedAnswerFormula + "</code></pre> but not <pre class='language-ltl'><code>" +  correctAnswerFormula + "</code></pre></p>";
        }

        // Render any trace diagrams in the feedback (e.g. misconception explainers)
        if (typeof TraceRenderer !== 'undefined') {
            feedback_div.querySelectorAll('.trace-diagram').forEach(function (el) {
                if (el.dataset.trace && !el.dataset.rendered) {
                    try {
                        TraceRenderer.render(el, JSON.parse(el.dataset.trace));
                        el.dataset.rendered = 'true';
                    } catch (e) { /* ignore rendering errors in feedback diagrams */ }
                }
            });
        }

        // Increment the incorrect count
        try {
            let incorrectCountElement = document.getElementById('incorrectCount');
            let currentCount = parseInt(incorrectCountElement.innerText);
            incorrectCountElement.innerText = currentCount + 1;
        } catch (error) {
            console.err("Something went wrong. Could not modify correctness count.");
        }
    }

    return correct;
}


function get_formula_for_MP_Classification(parent_node, question_type) {
    
    
    // ## If it is a eng to ltl, mp class is calculated from the correct answer
    // ## If it is a tracesat y_n question, mp class is calculated from the formula backing the tracesat question
    // ## If it is a tracesat multiple choice question, mp class is calculated from the formula backing the correct answer
    if (question_type == "trace_satisfaction_yn") {
        // I think this is correct
        let f = getQuestionText(parent_node);
        return f;
    }
    else if (question_type == "trace_satisfaction_mc") {
        // Both should work here I think.
        
        // let cr = getCorrectRadio(parent_node);
        // return cr.dataset.generatedfromformula;

        let f = getQuestionText(parent_node);
        return f;
    }
    else if (question_type == "english_to_ltl") {
        let cr = getCorrectRadio(parent_node);
        return cr.value;
    }
    else {
        return "";
    }
}


async function tracesatisfaction_mc_getfeedback(button) {

    const QUESTION_TYPE = "trace_satisfaction_mc";
    let parent_node = button.parentNode;
    let question_text = getQuestionText(parent_node);

    let selected_radio = getSelectedRadio(parent_node);
    if (selected_radio == null) {
        return;
    }

    let correct_option = getCorrectRadio(parent_node).value;
    let question_options = getQuestionOptions(parent_node);
    let correct = show_feedback(parent_node, QUESTION_TYPE);
    lockQuestionInteractions(parent_node);

    let data = {
        selected_option: selected_radio.value,
        correct_option: correct_option,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options,
        formula_for_mp_class: get_formula_for_MP_Classification(parent_node, QUESTION_TYPE),
        exercise: getExerciseName(),
        // The trace the student selected, so the server can explain why it
        // fails the formula.
        trace: selected_radio.value.trim()
    }
    let response = await postFeedback(data, QUESTION_TYPE);
    displayTraceSatFeedback(response, parent_node, QUESTION_TYPE);
}


async function tracesatisfaction_yn_getfeedback(button) {

    const QUESTION_TYPE = "trace_satisfaction_yn";
    let parent_node = button.parentNode;
    let question_text = getQuestionText(parent_node) + "\n" + getQuestionTrace(parent_node);

    let selected_radio = getSelectedRadio(parent_node);
    if (selected_radio == null) {
        return;
    }

    let correct_option = getCorrectRadio(parent_node).value;
    let question_options = getQuestionOptions(parent_node);
    let correct = show_feedback(parent_node, QUESTION_TYPE);
    lockQuestionInteractions(parent_node);

    let data = {
        selected_option: selected_radio.value,
        correct_option: correct_option,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options,
        formula_for_mp_class: get_formula_for_MP_Classification(parent_node, QUESTION_TYPE),
        exercise: getExerciseName(),
        // The question's trace, so the server can explain the correct verdict.
        trace: getQuestionTrace(parent_node).trim()
    }
    let response = await postFeedback(data, QUESTION_TYPE);
    displayTraceSatFeedback(response, parent_node, QUESTION_TYPE);
}

// Renders per-state satisfaction feedback for trace satisfaction questions:
// the relevant trace (the question's trace for y/n, the student's selected
// trace for mc) redrawn with each state marked ✓/✗ for whether the formula
// holds from that state onward.
function displayTraceSatFeedback(response, parent_node, question_type) {
    if (!response || response.error || !Array.isArray(response.state_satisfaction)
        || response.state_satisfaction.length === 0 || typeof TraceRenderer === 'undefined') {
        return;
    }

    let marks = response.state_satisfaction;
    let satisfies = marks[0];

    // Reuse the trace data already rendered in the question DOM.
    let traceDiv;
    if (question_type === "trace_satisfaction_yn") {
        traceDiv = parent_node.querySelector('.trace-diagram');
    } else {
        let selected = parent_node.querySelector('input[type=radio]:checked');
        let item = selected ? selected.closest('li') : null;
        traceDiv = item ? item.querySelector('.trace-diagram') : null;
    }
    if (!traceDiv || !traceDiv.dataset.trace) {
        return;
    }

    let traceData;
    try {
        traceData = JSON.parse(traceDiv.dataset.trace);
    } catch (e) {
        return;
    }
    let numStates = (traceData.prefix || []).length + (traceData.cycle || []).length;
    if (numStates !== marks.length) {
        return;
    }

    let subject = (question_type === "trace_satisfaction_yn") ? "This trace" : "The trace you selected";
    let verdict = satisfies
        ? subject + " <strong>does</strong> satisfy the formula."
        : subject + " does <strong>not</strong> satisfy the formula.";

    let el = document.createElement('div');
    el.innerHTML = "<p>" + verdict +
        " Each state below is marked with whether the formula holds from that state onward" +
        " (<span style='color:#198754;font-weight:700'>✓</span> holds," +
        " <span style='color:#dc3545;font-weight:700'>✗</span> fails)." +
        " A trace satisfies the formula exactly when it holds from the very first state.</p>" +
        "<div class='tracesat-feedback-trace'></div>";
    document.querySelector('#feedback').appendChild(el);

    TraceRenderer.render(el.querySelector('.tracesat-feedback-trace'), traceData, { stateMarks: marks });
}

async function englishtoltl_getfeedback(button) {


    const QUESTION_TYPE = "english_to_ltl";

    let parent_node = button.parentNode;
    let question_text = getQuestionText(parent_node);

    let selected_radio = getSelectedRadio(parent_node);
    if (selected_radio == null) {
        return;
    }
    let correct_option = getCorrectRadio(parent_node).value;
    let question_options = getQuestionOptions(parent_node);
    let correct = show_feedback(parent_node, QUESTION_TYPE);
    lockQuestionInteractions(parent_node);

    let data = {
        selected_option: selected_radio.value,
        correct_option: correct_option,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options,
        formula_for_mp_class: get_formula_for_MP_Classification(parent_node, QUESTION_TYPE),
        exercise: getExerciseName()
    }

    let response = await postFeedback(data, QUESTION_TYPE);
    displayServerResponse(response, selected_radio.value, correct_option);
}

function displayServerResponse(response, selected_formula, correct_formula) {

    let feedback_div = document.querySelector('#feedback');
    // First, parse the response.

    // TODO: Fix this, too rigid right now.
    if (typeof response === 'string') {
        feedback_div.innerHTML += response;
        return;
    }
    else if (response.error) {
        return;
    }
    // else if (response.message) {
    //     return response.message;
    // }

    let disjoint = response.disjoint;
    let subsumed = response.subsumed;
    let contained = response.contained;
    let equivalent = response.equivalent;

    let cewords = response.cewords;
    let traceDataList = response.trace_data;

    let r = (cewords.length > 0) ? Math.floor(Math.random() * cewords.length) : -1;
    let ce_trace = (cewords.length > 0) ? cewords[r] : null;
    let ce_trace_data = (cewords.length > 0) ? traceDataList[r] : null;

    var feedback_string = "";

    if (!ce_trace) {
        console.log("Could not generate a counterexample trace.")
    }

    let relation = equivalent ? 'equivalent'
        : disjoint ? 'disjoint'
        : subsumed ? 'subsumed'
        : contained ? 'contained'
        : 'overlap';

    if (relation === 'equivalent') {
        feedback_string += "Your selection is equivalent to the correct answer, meaning that it allows the same set of traces. However, the correct answer may represent a better way of expressing the solution.";
    }
    else {
        if (relation === 'disjoint') {
            feedback_string += "There are no possible traces that satisfy both the correct answer and your selection. ";
        }
        else if (relation === 'subsumed') {
            feedback_string += "Your selection is more restrictive than the correct answer. ";
        }
        else if (relation === 'contained') {
            feedback_string += "Your selection is more permissive than the correct answer. ";
        }
        else {
            feedback_string += "Your selection allows some traces accepted by the correct answer, but also permits other traces. ";
        }

        if (ce_trace) {
            // For 'subsumed' the counterexample goes the other way around.
            let ce_direction = (relation === 'subsumed')
                ? "the correct answer, but not your selection"
                : "your selection, but not the correct answer";
            feedback_string += "Here is a trace that satisfies " + ce_direction + ": <div id='generated_ltl_trace'></div>";
        }
    }

    feedback_string += "<div id='answer_relationship_diagram' class='mt-2'></div>";

    let responseAsHTMLElement = document.createElement('div');
    responseAsHTMLElement.innerHTML = feedback_string;
    feedback_div.appendChild(responseAsHTMLElement);

    let traceElement = document.getElementById('generated_ltl_trace');
    if (traceElement && ce_trace_data) {
        TraceRenderer.render(traceElement, ce_trace_data);
    }

    let diagramElement = document.getElementById('answer_relationship_diagram');
    if (diagramElement && typeof EulerDiagram !== 'undefined') {
        EulerDiagram.render(diagramElement, relation, {
            correctLabel: correct_formula,
            yourLabel: selected_formula,
            showTraceDot: !!ce_trace
        });
    }
}

async function postFeedback(data, questiontype) {
    try {
        uri = `/getfeedback/${questiontype}`;
        const response = await fetch(uri, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            const responseData = await response.json();
            return responseData;
        } 
    } catch (error) {
        console.error(error);
    }
    return { error: 'Failed to generate further feedback' }
}
