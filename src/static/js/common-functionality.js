function ensureUserId() {
    // Check if the cookie exists
    if (document.cookie.indexOf("ltluserid") === -1) {
        // Prompt the user for a value
        var userId = prompt("No userID found. Please enter your user ID:");

        // Set the cookie with the user ID
        document.cookie = "ltluserid=" + userId;
    }
}

document.addEventListener("DOMContentLoaded", function() {
    ensureUserId();

    // Get the value of the cookie ltluserid and store it in a variable
    var userId = "User: " + document.cookie.split('; ').find(row => row.startsWith('ltluserid')).split('=')[1];
    var uidfield = document.getElementById("userid_field");

    if (uidfield) {
        uidfield.innerText = userId;
    }

});