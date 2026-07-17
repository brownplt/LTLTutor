// Keep inline LTL fragments (notably misconception explainers) aligned with
// the syntax selected in the top bar. Elements marked <code class="ltlformula">
// are authored in Classic syntax; temporal operator tokens are rewritten for
// the selected syntax. Safe as pure token substitution because the tutor
// grammar only permits lowercase atoms, so a bare uppercase X/F/G/U is always
// an operator.
(function () {
    var OPERATOR_SPELLINGS = {
        Classic: { X: 'X', F: 'F', G: 'G', U: 'U' },
        Forge: { X: 'NEXT_STATE', F: 'EVENTUALLY', G: 'ALWAYS', U: 'UNTIL' },
        Electrum: { X: 'AFTER', F: 'EVENTUALLY', G: 'ALWAYS', U: 'UNTIL' }
    };

    function selectedSyntax() {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var pair = cookies[i].split('=');
            if (pair[0].trim() === 'ltlsyntax') {
                var value = decodeURIComponent(pair.slice(1).join('='));
                if (OPERATOR_SPELLINGS.hasOwnProperty(value)) {
                    return value;
                }
            }
        }
        return 'Classic';
    }

    function applySyntax(syntax, root) {
        var spellings = OPERATOR_SPELLINGS[syntax] || OPERATOR_SPELLINGS.Classic;
        var scope = root || document;
        scope.querySelectorAll('code.ltlformula').forEach(function (element) {
            if (element.dataset.classic === undefined) {
                element.dataset.classic = element.textContent.trim();
            }
            element.textContent = element.dataset.classic.replace(
                /\b[XFGU]\b/g,
                function (token) { return spellings[token]; }
            );
        });
    }

    window.LtlSyntax = {
        apply: applySyntax,
        selected: selectedSyntax
    };

    document.addEventListener('DOMContentLoaded', function () {
        applySyntax(selectedSyntax());
    });
})();

function isElementVisibleInViewport(element, margin = 24) {
    if (!element) {
        return false;
    }

    const rect = element.getBoundingClientRect();
    const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
    const topBoundary = margin;
    const bottomBoundary = viewportHeight - margin;

    return rect.bottom > topBoundary && rect.top < bottomBoundary;
}

function removeFeedbackPrompts() {
    document.querySelectorAll('.view-feedback-prompt').forEach((prompt) => prompt.remove());
}

function addFeedbackPrompt(triggerButton, feedbackElement) {
    if (!triggerButton) {
        return;
    }

    const jumpButton = document.createElement('button');
    jumpButton.type = 'button';
    jumpButton.className = 'btn btn-link btn-sm p-0 ml-2 align-baseline view-feedback-prompt view-feedback-prompt-pulse-once';
    jumpButton.textContent = 'View feedback ↓';
    jumpButton.setAttribute('aria-label', 'View updated feedback');

    jumpButton.addEventListener('click', () => {
        feedbackElement.scrollIntoView({ behavior: 'smooth', block: 'start', inline: 'nearest' });
        jumpButton.remove();
    });

    triggerButton.insertAdjacentElement('afterend', jumpButton);
}

function scrollToFeedback(triggerButton = null) {

    setTimeout(() => {
        const feedbackElement = document.getElementById('feedback');
        if (!feedbackElement) {
            return;
        }

        // Remove stale prompts from previous questions/checks.
        removeFeedbackPrompts();

        // Keep user control: only offer an explicit jump action if feedback is off-screen.
        if (isElementVisibleInViewport(feedbackElement)) {
            return;
        }

        addFeedbackPrompt(triggerButton, feedbackElement);
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
