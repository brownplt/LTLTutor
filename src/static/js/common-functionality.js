
class NodeRepr {

    constructor(vars) {
        this.vars = vars.trim();
        this.id = Math.random().toString(36).substring(2, 8);
    }

    toString() {
        return `${this.id}["${this.vars}"]`;
    }
}

function ensureUserId() {
    // Check if the cookie exists
    if (document.cookie.indexOf("ltluserid") === -1) {
        // Prompt the user for a value
        var userId = prompt("No userID found. Please enter your user ID:");

        // Set the cookie with the user ID
        document.cookie = "ltluserid=" + userId;
    }
}

document.addEventListener("DOMContentLoaded", function () {
    ensureUserId();

    // Get the value of the cookie ltluserid and store it in a variable
    var userId = "User: " + document.cookie.split('; ').find(row => row.startsWith('ltluserid')).split('=')[1];
    var uidfield = document.getElementById("userid_field");

    if (uidfield) {
        uidfield.innerText = userId;
    }

    // Call build graph for each trace element, ie every element with class "ltltrace"
    let traceElements = document.querySelectorAll('.ltltrace');
    traceElements.forEach(traceElement => {
        buildGraph(traceElement);
        mermaid.init(undefined, traceElement);
    });

});


function buildGraph(traceElement) {
    let trace = traceElement.innerText;
    let edges = edgesFromSpotString(trace);
    let diagramText = mermaidGraphFromEdgesList(edges);
    traceElement.setAttribute('aria-label', trace);
    traceElement.setAttribute('role', 'img');

    traceElement.textContent = diagramText;    
}


function edgesFromSpotString(sr) {

    sr = sr.trim();

    function getCycleContent(str) {
        let match = str.match(/.*\{([^}]*)\}/);
        return match ? match[1] : "";
    }

    if (sr == "") {
        return [];
    }

    let parts = sr.split(';');
    let edges = []


    let states = parts.map(part => new NodeRepr(part));


    let cycleCandidate = states[states.length - 1];

    // TODO: AFAIK, but look out:
    //Cycle must happen at the very end, we cannot have nested cycles 

    if (cycleCandidate.vars.startsWith('cycle')) {

        let cycled_content = getCycleContent(cycleCandidate.vars);
        let cycle_states = cycled_content.split(';').map(part => new NodeRepr(part));
        // Add the cycle. So now we have at least 2 states in the array.
        cycle_states.push(cycle_states[0])

        // Remove the last element from states array
        states.pop();
        states = states.concat(cycle_states);
    }

    // For each part, get the next part and add it to the edges array
    for (let i = 1; i < states.length; i += 1) {
        let current = states[i - 1];
        let next = states[i];
        edges.push([current, next]);
    }
    return edges;
}


function mermaidGraphFromEdgesList(edges) {

    let diagramText = 'flowchart LR;\n';

    edges.forEach(edge => {
        diagramText += `${edge[0].toString()}-->${edge[1].toString()};`;
    });

    return diagramText;
}
