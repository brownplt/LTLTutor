

function getQuestionText(parentNode) {
    return parentNode.querySelector('.card-title').innerText;
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

function show_feedback(parent_node) {

    let all_radios = parent_node.querySelectorAll('input[type=radio]');
    Array.from(all_radios).forEach(radio => {
        //radio.parentNode.style.backgroundColor = "transparent";
        radio.parentNode.style.outline = "none";
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


        selected_radio.parentNode.style.outline = "2px solid green";


        // Add a message to the feedback div
        feedback_div.innerHTML = "<p> Correct answer! 🎉🥳 Great job! </p>";
        feedback_div.classList.add('alert');
        feedback_div.classList.add('alert-success');
        feedback_div.classList.remove('alert-warning');

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
        selected_radio.parentNode.style.outline = "2px solid red";
        correct_radio.parentNode.style.outline = "2px solid green";

        misconception_string = selected_radio.dataset.misconceptions.replace(/'/g, '"');
        let misconceptions = JSON.parse(misconception_string);
        console.log(misconceptions);
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is: <code>" + correct_option + "</code></p>";
        feedback_div.classList.add('alert');
        feedback_div.classList.remove('alert-success');
        feedback_div.classList.add('alert-warning');
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

async function tracesatisfaction_getfeedback(button) {

    let parent_node = button.parentNode;
    let question_text = getQuestionText(parent_node);

    let selected_radio = getSelectedRadio(parent_node);
    if (selected_radio == null) {
        return;
    }

    let correct_option = getCorrectRadio(parent_node).value;
    let question_options = getQuestionOptions(parent_node);
    let correct = show_feedback(parent_node);

    let data = {
        selected_option: selected_radio.value,
        correct_option: correct_option,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options
    }
    let response = await postFeedback(data, "trace_satisfaction");
}

async function englishtoltl_getfeedback(button) {
    let parent_node = button.parentNode;
    let question_text = getQuestionText(parent_node);

    let selected_radio = getSelectedRadio(parent_node);
    if (selected_radio == null) {
        return;
    }
    let correct_option = getCorrectRadio(parent_node).value;
    let question_options = getQuestionOptions(parent_node);
    let correct = show_feedback(parent_node);


    // TODO: SOme kind of error getting correct_option

    let data = {
        selected_option: selected_radio.value,
        correct_option: correct_option,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options
    }

    let response = await postFeedback(data, "english_to_ltl");
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

    let disjoint = response.disjoint;
    let subsumed = response.subsumed;
    let contained = response.contained;
    let cewords = response.cewords;
    let ce_trace = (cewords.length > 0) ? cewords[Math.floor(Math.random() * cewords.length)] : null;



    function get_mermaid_diagram(trace) {
        let edges = edgesFromSpotString(trace);
        let diagramText = mermaidGraphFromEdgesList(edges);
        return diagramText;
    }

    let ce_trace_img =  ce_trace ? get_mermaid_diagram(ce_trace) : "";
    ce_trace_img = "<div id='generated_ltl_trace'>" + ce_trace_img + "</div>";

    var feedback_string = "";

    if (!ce_trace) {
        console.log("Could not generate a counterexample trace.")
    }

    if (disjoint) {
        feedback_string += "There are no possible traces that satisfy both the correct answer and your selection. ";

        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }

        feedback_string += "<br> <img src='/static/img/disjoint.png' alt='disjoint' > <br> ";

    }
    else if (subsumed) {
        feedback_string += "Your selection is more restrictive than the correct answer.";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies the correct answer, but not your selection: " + ce_trace_img;
        }
        feedback_string += "<br> <img src='/static/img/subsumes.png' alt='subsumption' > <br> ";


    }
    else if (contained) {
        feedback_string += "Your selection is more permissive than the correct answer. ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }
        feedback_string += "<br> <img src='/static/img/contained.png' alt='containment' > <br> ";

    }
    else {
        feedback_string += "Your selection allows some traces accepted by the correct answer, but also permits other traces. ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace_img;
        }
        feedback_string += "<br> <img src='/static/img/overlap.png' alt='overlapping answers' > <br> ";
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
