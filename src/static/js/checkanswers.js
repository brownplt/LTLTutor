async function getfeedback(button) {
    
    let parent_node = button.parentNode;
    

    //parent node has a list of radio buttons. Find the selected
    // radio button
    let selected_radio = parent_node.querySelector('input[type=radio]:checked');

    //if no radio button is selected, show an alert that no radio button is selected
    if(selected_radio == null) {
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
        feedback_div.innerHTML = "<p>That's not correct 😕 Don't worry, keep trying! The correct answer is: " + correct_option.value + "</p>";
    }



    let data = {
        selected_option: selected_option,
        correct_option: correct_option.value,
        correct: correct,
        misconceptions: selected_radio.dataset.misconceptions
    }

    let response = await postFeedback(data);
    let responseAsHTMLElement = document.createElement('div');
    responseAsHTMLElement.innerHTML = response.feedback;
    feedback_div.appendChild(responseAsHTMLElement);

    }


async function postFeedback(data) {
    try {
        const response = await fetch('/getfeedback', {
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
