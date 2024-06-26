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

        function getTraceStepperButtonHtml() {
            if (question_type == "trace_satisfaction_yn" || question_type == "trace_satisfaction_mc") {
                var formulaForStepper = get_formula_for_MP_Classification(parent_node, question_type);
                var qtrace = (question_type == "trace_satisfaction_yn") ? getQuestionTrace(parent_node) : getSelectedRadio(parent_node).value;
                
                
                // TODO: There is a sort of bug here! The trace being passed is not alwayts the correct one!
                var fv = `
                        <form action="/stepper" method="post" target="_blank">
                            <input type="hidden" name="formula" value='${formulaForStepper}'>
                            <input type="hidden" name="trace" value='${qtrace}'>
                            <button type="submit" class="btn btn-secondary">Step through the trace and your answer.</button>
                        </form>
                        `
                return fv;
            }
            return "";
        }



        correct_radio.parentNode.parentNode.classList.add("bg-success");
        selected_radio.parentNode.parentNode.classList.add("bg-danger");

        misconception_string = selected_radio.dataset.misconceptions.replace(/'/g, '"');
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is highlighted in green (i.e: <code>" + correct_option + "</code> )" +  getTraceStepperButtonHtml() +  "</p>";
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
    displayServerResponse(response);
}

function displayServerResponse(response) {

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

    // TODO: Fix this to allow for different response feedback.

    let disjoint = response.disjoint;
    let subsumed = response.subsumed;
    let contained = response.contained;
    let equivalent = response.equivalent;

    // TODO: Switch on equivalent

    let cewords = response.cewords;
    let wordsasmermaid = response.mermaid;

    let r = (cewords.length > 0) ? Math.floor(Math.random() * cewords.length) : -1;
    let ce_trace = (cewords.length > 0) ? cewords[r] : null;
    let ce_mermaid = (cewords.length > 0) ? wordsasmermaid[r] : null;


    // let ce_trace_img =  ce_trace ? get_mermaid_diagram(ce_trace) : "";
    ce_trace_img = "<pre id='generated_ltl_trace' class='mermaid'>" + ce_mermaid + "</pre> <br> Alt Trace: " + ce_trace;

    var feedback_string = "";

    if (!ce_trace) {
        console.log("Could not generate a counterexample trace.")
    }

    if (equivalent) {
        feedback_string += "Your selection is equivalent to the correct answer, meaning that it allows the same set of traces. However, the correct answer may represent a better way of expressing the solution.";
    }
    else if (disjoint) {
        feedback_string += "There are no possible traces that satisfy both the correct answer and your selection. ";

        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }

        feedback_string += "<br> <img class='img-fluid ' style='max-height: 400px; width: auto;' src='/static/img/disjoint.png' alt='Euler diagram of two disjoint sets: a green set (representing the correct answer) and a red set (representing your answer).' > ";

    }
    else if (subsumed) {
        feedback_string += "Your selection is more restrictive than the correct answer.";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies the correct answer, but not your selection: " + ce_trace_img;
        }
        feedback_string += "<br> <img class='img-fluid ' style='max-height: 400px; width: auto;' src='/static/img/subsumes.png' alt='Euler diagram of a green set (representing the correct answer) subsuming a red set (representing your answer).' >  ";


    }
    else if (contained) {
        feedback_string += "Your selection is more permissive than the correct answer. ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }
        feedback_string += "<br> <img class='img-fluid ' style='max-height: 400px; width: auto;' src='/static/img/contained.png' alt='Euler diagram of a green set (representing the correct answer) being subsumed by a red set (representing your answer).' > ";

    }
    else {
        feedback_string += "Your selection allows some traces accepted by the correct answer, but also permits other traces. ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }
        feedback_string += "<br> <img class='img-fluid ' style='max-height: 400px; width: auto;' src='/static/img/overlap.png' alt='Euler diagram of two overlapping, but not contained sets: a green set (representing the correct answer) and a red set (representing your answer).' >  ";
    }

    let responseAsHTMLElement = document.createElement('div');
    responseAsHTMLElement.innerHTML = feedback_string;
    feedback_div.appendChild(responseAsHTMLElement);

    let traceElement = document.getElementById('generated_ltl_trace');
    if (traceElement) {
        mermaid.init(undefined, traceElement);
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
