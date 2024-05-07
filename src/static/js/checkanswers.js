/// TODO: Clean this up, unify functions, etc.


async function tracesat_getfeedback(button) {

    let parent_node = button.parentNode;
    let question_text = parent_node.querySelector('.card-title').innerText;


    let all_radios = parent_node.querySelectorAll('input[type=radio]');

    // For each radio button, make the background transparent
    Array.from(all_radios).forEach(radio => {
        radio.parentNode.style.backgroundColor = "transparent";
    });
    
    // For each radio button, get value and data-misconception fields
    var question_options = Array.from(all_radios).map(r => ({
        value: r.value,
        misconceptions: r.dataset.misconceptions
    }));

    let selected_radio = parent_node.querySelector('input[type=radio]:checked');

    //if no radio button is selected, show an alert that no radio button is selected
    if (selected_radio == null) {
        alert("Please select an option");
        return;
    }

    //get the selected option
    let selected_option = selected_radio.value;

    // There is a radio button where the 'dataset.correct' attribute is set to true
    // Find that radio button
    // Select the radio button where 'dataset.correct' is true
    var correct_option = parent_node.querySelector('input[data-correct="True"]');

    //Get the div with id feedback
    let feedback_div = document.querySelector('#feedback');
    let correct = selected_option == correct_option.value;

    if (selected_option == correct_option.value) {
        // Make the background of the selected radio button green
        selected_radio.parentNode.style.backgroundColor = "green";
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p> Correct answer! 🎉🥳 Great job! </p>";
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
        selected_radio.parentNode.style.backgroundColor = "red";
        correct_option.parentNode.style.backgroundColor = "green";

        misconception_string = selected_radio.dataset.misconceptions.replace(/'/g, '"');
        let misconceptions = JSON.parse(misconception_string);
        console.log(misconceptions);
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is: <code>" + correct_option.value + "</code></p>";

        // Increment the incorrect count
        try {
            let incorrectCountElement = document.getElementById('incorrectCount');
            let currentCount = parseInt(incorrectCountElement.innerText);
            incorrectCountElement.innerText = currentCount + 1;
        } catch (error) {
            console.err("Something went wrong. Could not modify correctness count.");
        }
    }

    let data = {
        selected_option: selected_option,
        correct_option: correct_option.value,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options
    }
    let response = await postFeedback(data, "trace_satisfaction");
    console.log(response);
}

async function engtoltl_getfeedback(button) {

    let parent_node = button.parentNode;


    let question_text = parent_node.querySelector('.card-title').innerText;



    let all_radios = parent_node.querySelectorAll('input[type=radio]');

    // For each radio button, make the background transparent
    Array.from(all_radios).forEach(radio => {
        radio.parentNode.style.backgroundColor = "transparent";
    });


    // For each radio button, get value and data-misconception fields
    var question_options = Array.from(all_radios).map(r => ({
        value: r.value,
        misconceptions: r.dataset.misconceptions
    }));

    let selected_radio = parent_node.querySelector('input[type=radio]:checked');

    //if no radio button is selected, show an alert that no radio button is selected
    if (selected_radio == null) {
        alert("Please select an option");
        return;
    }

    //get the selected option
    let selected_option = selected_radio.value;

    // There is a radio button where the 'dataset.correct' attribute is set to true
    // Find that radio button
    // Select the radio button where 'dataset.correct' is true
    var correct_option = parent_node.querySelector('input[data-correct="True"]');






    //Get the div with id feedback
    let feedback_div = document.querySelector('#feedback');


    let correct = selected_option == correct_option.value;

    if (selected_option == correct_option.value) {
        // Make the background of the selected radio button green
        selected_radio.parentNode.style.backgroundColor = "green";
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p> Correct answer! 🎉🥳 Great job! </p>";
    }
    else {




        selected_radio.parentNode.style.backgroundColor = "red";
        correct_option.parentNode.style.backgroundColor = "green";

        misconception_string = selected_radio.dataset.misconceptions.replace(/'/g, '"');
        let misconceptions = JSON.parse(misconception_string);
        console.log(misconceptions);
        // Add a message to the feedback div
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is: <code>" + correct_option.value + "</code></p>";
    }



    let data = {
        selected_option: selected_option,
        correct_option: correct_option.value,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions,
        question_text: question_text,
        question_options: question_options
    }

    let response = await postFeedback(data, "english_to_ltl"); ``
    displayServerResponse(response);
}



function displayServerResponse(response) {

    let feedback_div = document.querySelector('#feedback');
    // First, parse the response.

    let disjoint = response.disjoint;
    let subsumed = response.subsumed;
    let contained = response.contained;
    let cewords = response.cewords;


    let ce_trace = (cewords.length > 0) ? cewords[Math.floor(Math.random() * cewords.length)] : null;

    var feedback_string = "";

    if (disjoint) {
        feedback_string += "There are no possible traces that satisfy both the correct answer and your selection. ";


        // I want to show img/disjoint.png here
        feedback_string += "<br> <img src='/static/img/disjoint.png' alt='disjoint' > <br> ";

        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace;
        }

    }
    else if (subsumed) {
        feedback_string += "Your selection is an overconstraint of the correct answer. That is, your selection is more restrictive than the correct answer.";
        feedback_string += "<br> <img src='/static/img/subsumes.png' alt='subsumption' > <br> ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies the correct answer, but not your selection: " + ce_trace;
        }

    }
    else if (contained) {
        feedback_string += "Your selection is an underconstraint of the correct answer. ";
        feedback_string += "<br> <img src='/static/img/contained.png' alt='containment' > <br> ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace;
        }
    }
    else {
        feedback_string += "Your selection allows some traces accepted by the correct answer, but also permits other traces. ";
        feedback_string += "<br> <img src='/static/img/overlap.png' alt='overlapping answers' > <br> ";
        if (ce_trace) {
            feedback_string += "Here is a trace that satisfies your selection, but not the correct answer: " + ce_trace;
        }
    }


    let responseAsHTMLElement = document.createElement('div');
    responseAsHTMLElement.innerHTML = feedback_string;
    feedback_div.appendChild(responseAsHTMLElement);


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
        } else {
            return { error: 'Failed to generate feedback' }
        }
    } catch (error) {
        console.error(error);
    }
}
