import {LTLNode, BinaryOperatorNode, UnaryOperatorNode, LiteralNode, UntilNode} from "./ltlnode";

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


class MutationResult {
    node: LTLNode;
    misconception: MisconceptionCode | null = null;

    constructor(node: LTLNode, misconception: MisconceptionCode | null = null) {
        this.node = node;
        this.misconception = misconception;
    }

}


// Takes a LTLNode and manipulates it to be in line with the misconception

function applyMisconception(node: LTLNode, misconception: MisconceptionCode): MutationResult {
    switch (misconception) {
        case MisconceptionCode.Precedence:
            return applyTilFirst(node, applyPrecedence);
        case MisconceptionCode.ReasonableVariant:

            // Remove

            //return applyReasonableVariant(node);
        case MisconceptionCode.BadProp:


            // This is the equiv of a syntax error right?

            //return applyBadProp(node);
        case MisconceptionCode.BadStateIndex:
            //return applyBadStateIndex(node);
        case MisconceptionCode.BadStateQuantification:
            //return applyBadStateQuantification(node);
        case MisconceptionCode.ExclusiveU:
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
            return new MutationResult(node);

    }
}




// TODO: There *must* be a simpler way to do this
// Applies f on the LTL formula up til the first time it changes a node
function applyTilFirst(node : LTLNode, f : (node: LTLNode) => MutationResult ) : MutationResult {


    // See if it applies at the top level
    let res = f(node);
    if (res.misconception) {
        return res;
    }

    // if unary operator, apply to operand and see if it changed.
    if (node instanceof UnaryOperatorNode) {
        let res = applyTilFirst(node.operand, f);
        node.operand = res.node;
        res.node = node;
        return res;
    }


     if (node instanceof BinaryOperatorNode) {
        // TODO: Maybe randomize the choice here
        let res_left = applyTilFirst(node.left, f);
        let res_right = applyTilFirst(node.right, f);

        const randomIndex = Math.floor(Math.random() * 2);
        var choose_left = res_left.misconception && (!res_right.misconception  || randomIndex == 0  );
        var choose_right = res_right.misconception && (!res_left.misconception || randomIndex == 1);

        if (choose_left) {
            node.left = res_left.node;
            res_left.node = node;
            return res_left;
        } else if (choose_right) {
            node.right = res_right.node;
            res_right.node = node;
            return res_right;
        }
     }

    // If nothing applied, unchanged.
    return new MutationResult(node);
}


// Changes all precedences in the LTL formula
// Perhaps we need to change fewer, some at random. Let's figure it out.
function applyPrecedence(node : LTLNode) : MutationResult {


    if (node instanceof LiteralNode) {
        return new MutationResult(node);
    }

    if (node instanceof UnaryOperatorNode) {
        let res = applyPrecedence(node.operand);
        node.operand = res.node;
        res.node = node;
        return res;
    }

    if (node instanceof BinaryOperatorNode) {
        // TODO: Is this right?

        // node.left = applyPrecedence(node.left);
        // node.right = applyPrecedence(node.right);

        // Check if we need to adjust precedence based on child nodes
        if (node.right instanceof BinaryOperatorNode) {
            // Perform rotation to adjust precedence
            let newTop = node.right;
            node.right = newTop.left;
            newTop.left = node;

            return new MutationResult(newTop, MisconceptionCode.Precedence);
        }
    }

    return new MutationResult(node);
}






function applyExclusiveU(node : LTLNode) : MutationResult {

    if (node instanceof UnaryOperatorNode) {
        let res = applyExclusiveU(node.operand);
        node.operand = res.node;
        res.node = node;
        return res;
    }
    else if (node instanceof BinaryOperatorNode && node.operator == "U") {
         // Find an instance of  /  x U ((not x) and y) and replace it with x U y
        let x = node.left;
        let rhs = node.right;

        if (rhs instanceof BinaryOperatorNode && rhs.operator == "and") {

            let y = rhs.right;

            if (rhs.left instanceof UnaryOperatorNode && rhs.left.operator == "!" && LTLNode.equiv(rhs.left.operand, x)) {
                return new MutationResult(new UntilNode(x, y), MisconceptionCode.ExclusiveU);
            }
        }
    }
    return new MutationResult(node);
}