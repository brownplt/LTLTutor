
const USERIDKEY = "ltluserid";

function getCookie(name) {
    let cookieArray = document.cookie.split(';');
    for(let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i];
        while (cookie.charAt(0) == ' ') {
            cookie = cookie.substring(1);
        }
        if (cookie.indexOf(name) == 0) {
            return cookie.substring(name.length + 1);
        }
    }
    return "";
}



function ensureUserId() {
    // Check if the cookie exists
    var noUserId = document.cookie.indexOf(USERIDKEY) === -1 || getCookie(USERIDKEY) == null || getCookie(USERIDKEY) == "";

    if (noUserId) {

        $('#userIdModal').removeClass('d-none');
        // Make a request to the server to get a new user ID
        fetch('/getuserid')
            .then(response => response.text())  // convert the response to text
            .then(userId => {


                const date = new Date();
                date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000));
                const expires = ";expires=" + date.toUTCString();
                // Set the cookie with the user ID
                //TODO: Make this a persistent cookie
                document.cookie = USERIDKEY + "=" + userId + expires + ";path=/";
            })
            .catch(error => console.error('Error Generating User Id:', error));
    }
    
}

$(document).ready(function() {
    ensureUserId();

    // Get the value of the cookie ltluserid and store it in a variable
    var userId = getCookie(USERIDKEY);




    var uidfield = document.getElementById("userid_field");

    if (uidfield) {
        uidfield.innerText = "User: " +  userId;
    }
});

