
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


function generateUUID() { 
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = Math.random() * 16 | 0,
            v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

function ensureUserId() {
    // Check if the cookie exists

    var noUserId = document.cookie.indexOf(USERIDKEY) === -1 || getCookie(USERIDKEY) == null || getCookie(USERIDKEY) == "";

    if (noUserId) {
        // Generate UserId from a GUID
        var userId = generateUUID();
        // Set the cookie with the user ID
        document.cookie = "ltluserid=" + userId;
    }
}

$(document).ready(function() {
    ensureUserId();

    // Get the value of the cookie ltluserid and store it in a variable
    var userId = "User: " + document.cookie.split('; ').find(row => row.startsWith('ltluserid')).split('=')[1];
    var uidfield = document.getElementById("userid_field");

    if (uidfield) {
        uidfield.innerText = userId;
    }
});

