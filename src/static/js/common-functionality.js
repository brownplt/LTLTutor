
const USERIDKEY = "ltluserid";

function getCookie(name) {
    let cookieArray = document.cookie.split(';');
    for (let i = 0; i < cookieArray.length; i++) {
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



async function ensureUserId() {
    // Check if the cookie exists
    var noUserId = document.cookie.indexOf(USERIDKEY) === -1 || getCookie(USERIDKEY) == null || getCookie(USERIDKEY) == "";
    var userId = Math.random().toString(36).substring(2, 15)
    if (noUserId) {
        $('#userIdModal').removeClass('d-none');
        try {
            const response = await fetch('/getuserid');
            userId = await response.text();
        } catch (error) {
            console.error('Error Generating User Id:', error);
            console.log("Defaulting to less memorable user ID: " + userId)

        }
        // Set the cookie with the user ID
        const date = new Date();
        date.setTime(date.getTime() + (365 * 24 * 60 * 60 * 1000));
        const expires = ";expires=" + date.toUTCString();

        document.cookie = USERIDKEY + "=" + userId + expires + ";path=/";
    }

}

$(document).ready(function () {
    ensureUserId()
    .then(() => {
        // Get the value of the cookie ltluserid and store it in a variable
        var userId = getCookie(USERIDKEY);
        var uidfield = document.getElementById("userid_field");

        if (uidfield) {
            uidfield.innerText = "User: " + userId;
        }
    });
});



function scrollToFeedback() {

    setTimeout(() => {
        var element = document.getElementById("feedback");
        element.scrollIntoView({behavior: "smooth", block: "start", inline: "start"});
    }, 100);

}
