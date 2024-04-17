import {LTLNode, BinaryOperatorNode, UnaryOperatorNode, LiteralNode} from "./ltlnode";

enum MisconceptionCode {
    /** Applies to LTL formulas that are correct up to missing parentheses. */
    Precedence = "Precedence",

    /** Applies to LTL formulas that are correct for an unintended reading of the question. */
    ReasonableVariant = "ReasonableVariant",

    /** Used when an answer is convoluted and/or ambiguous, with no other tags applied. */
    Unlabeled = "Unlabeled",

    /** Applies to responses that misuse a logical operator or an atomic symbol. */
    BadProp = "BadProp",

    /** Applies to responses that use a correct term at an incorrect state index. */
    BadStateIndex = "BadStateIndex",

    /** Applies to responses that misuse or swap a fan-out operator (F, G, U). */
    BadStateQuantification = "BadStateQuantification",

    /** Applies to responses assuming 'until' is satisfied only when both the right subterm and the negation of the left subterm hold. */
    ExclusiveU = "ExclusiveU",

    /** Applies to responses that either ignore or introduce an F quantifier. */
    ImplicitF = "ImplicitF",

    /** Applies to responses that either ignore or introduce a G quantifier. */
    ImplicitG = "ImplicitG",

    /** Applies to underconstrained responses not covered by the ImplicitF and ImplicitG tags. */
    OtherImplicit = "OtherImplicit",

    /** Applies to responses that confuse the U operator with the weak variant W, which does not guarantee that its second subterm eventually holds. */
    WeakU = "WeakU"
}

export default MisconceptionCode;



function getRandomMisconceptionCode(): MisconceptionCode {
    const values = Object.values(MisconceptionCode);
    const randomIndex = Math.floor(Math.random() * values.length);
    return values[randomIndex];
}


// Takes a LTLNode and manipulates it to be in line with the misconception

function applyMisconception(node: LTLNode, misconception: MisconceptionCode): LTLNode {
    switch (misconception) {
        case MisconceptionCode.Precedence:
            return applyTilFirst(node, applyPrecedence);
        case MisconceptionCode.ReasonableVariant:
            //return applyReasonableVariant(node);
        case MisconceptionCode.BadProp:
            //return applyBadProp(node);
        case MisconceptionCode.BadStateIndex:
            //return applyBadStateIndex(node);
        case MisconceptionCode.BadStateQuantification:
            //return applyBadStateQuantification(node);
        case MisconceptionCode.ExclusiveU:
                // TODO: Find an instance of  /  x U ((not x) and y) and replace it with x U y
                //  x U ((not x) and y) but subject wrote x U y


            return applyTilFirst(node, applyExclusiveU);
        case MisconceptionCode.ImplicitF:
            //return applyImplicitF(node);
        case MisconceptionCode.ImplicitG:
            //return applyImplicitG(node);
        case MisconceptionCode.OtherImplicit:
            //return applyOtherImplicit(node);
        case MisconceptionCode.WeakU:
            //return applyWeakU(node);
        default:
            return node;

        return node;
    }
}





// Applies f on the LTL formula up til the first time it changes a node
function applyTilFirst(node : LTLNode, f : (node: LTLNode) => LTLNode ) : LTLNode {


    if (node instanceof LiteralNode) {
        return f(node);
    }

    if (node instanceof UnaryOperatorNode) {
            
        node.operand = f(node.operand);
    }
    else if (node instanceof BinaryOperatorNode) {

        let op_left = f(node.left);
        let op_right = f(node.right);

        // TODO: Equality check might not work here

        if (op_left != node.left) {
            node.left = op_left;
        }
        else if (op_right != node.right) {
            node.right = op_right;
        }
    }

    return node;
}


// Changes all precedences in the LTL formula
// Perhaps we need to change fewer, some at random. Let's figure it out.
function applyPrecedence(node : LTLNode) : LTLNode {


    if (node instanceof LiteralNode) {
        return node;
    }

    if (node instanceof UnaryOperatorNode) {
            
        node.operand = applyPrecedence(node.operand);
        return node;
    }




    if (node instanceof BinaryOperatorNode) {


        // Make a random decision on which side to change

        node.left = applyPrecedence(node.left);
        node.right = applyPrecedence(node.right);

        // Check if we need to adjust precedence based on child nodes
        if (node.right instanceof BinaryOperatorNode) {
            // Perform rotation to adjust precedence
            let newTop = node.right;
            node.right = newTop.left;
            newTop.left = node;

            return applyPrecedence(newTop);  // Continue to adjust up the tree
        }
        else if (node.left instanceof BinaryOperatorNode) {
            // Perform rotation to adjust precedence
            let newTop = node.left;
            node.left = newTop.right;
            newTop.right = node;

            return applyPrecedence(newTop);  // Continue to adjust up the tree
        }
    }

    return node;
}






function applyExclusiveU(node : LTLNode) : LTLNode {

    // TODO: Find an instance of  /  x U ((not x) and y) and replace it with x U y
    //  x U ((not x) and y) but subject wrote x U y


    // This only applies it at the top level, see if we can apply it at various levels.

    if (node instanceof BinaryOperatorNode && node.operator === "U") {
        if (node.left instanceof LiteralNode && node.right instanceof BinaryOperatorNode && node.right.operator === "and") {
            const leftOperand = node.left;
            const rightOperand = node.right.right;
            if (node.right.left instanceof UnaryOperatorNode && node.right.left.operator === "not" && node.right.left.operand === leftOperand) {
                return new BinaryOperatorNode("U", leftOperand, rightOperand);
            }
        }
    }
    return node
}