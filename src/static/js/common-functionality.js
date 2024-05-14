
class NodeRepr {

    constructor(vars) {

        this.vars = vars.trim();

        // Do we want to only choose one of the 'ors'?
        // If so, we can choose a random one
        if (this.vars.includes('|') && !this.vars.includes('cycle')) {


            let ors = this.vars.split('|');
            this.vars = ors[Math.floor(Math.random() * ors.length)];
            
            // Deal with cycles later
            console.log("Found OR in vars and chose ", this.vars)
        }

        this.id = Math.random().toString(36).substring(2, 8);
    }

    toString() {
        // TODO: Do we want &s?
        // return `${this.id}["${this.vars.replace(/&/g, ',')}"]`;
        return `${this.id}["${this.vars}"]`;
    }
}

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


    try {
        //Call ensure_literals on each state
        states = states.map(state => ensure_literals(state));
    }
    catch (e) {
        console.log("Ensure literals failed")
        console.log(e);

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

function ensure_literals(node) {

    if (typeof literals === 'undefined' || literals === null) {
        return node;
    }


    let vars = node.vars.trim();

    if (vars == "1") {
        let xs = literals.join(" & ");
        node.vars = xs;
        return node;
    }

    if (vars == "0") {
        let xs = literals.map(literal => `!${literal}`).join(" & ");
        node.vars = xs;
        return node;
    }

    // I want a list of all the lowercase words in vars
    let vars_words = vars.match(/\b[a-z0-9]+\b/g);

    // If any word in literals is not in vars_words, we add it ( or ! it) to vars
    let missing_literals = literals.filter(literal => !vars_words.includes(literal));

    for (let literal of missing_literals) {
        // TODO: Choose between adding the literal or adding the negation of the literal
        let x = Math.random() < 0.5 ? literal : `!${literal}`;
        vars = `${vars} & ${x}`;
    }
    node.vars = vars;
    return node;
}