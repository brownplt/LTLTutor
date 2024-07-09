



function scrollToFeedback() {

    setTimeout(() => {
        var element = document.getElementById("feedback");
        element.scrollIntoView({behavior: "smooth", block: "start", inline: "start"});
    }, 100);

}

document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.help').forEach(function(element) {
        element.addEventListener('click', function() {
            // Extract the text content of the parent .help element
            var helpText = this.innerHTML;
            
            // Set the content of the modal dynamically
            document.querySelector('#genericHelpModal .modal-body').innerHTML = helpText;
            
            // Trigger the modal to open
            $('#genericHelpModal').modal('show');
        });
    });
});