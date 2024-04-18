import {LTLNode, BinaryOperatorNode, UnaryOperatorNode, LiteralNode, UntilNode, NotNode, FinallyNode, GloballyNode, AndNode, ImpliesNode, NextNode, EquivalenceNode, OrNode} from "./ltlnode";

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
        
        case MisconceptionCode.BadStateIndex:
            return applyTilFirst(node, applyBadStateIndex);
        case MisconceptionCode.BadStateQuantification:
            return applyTilFirst(node, applyBadStateQuantification);
        case MisconceptionCode.ExclusiveU:
            return applyTilFirst(node, applyExclusiveU);
        case MisconceptionCode.ImplicitF:
            return applyTilFirst(node, applyImplicitF);
        case MisconceptionCode.ImplicitG:
            return applyTilFirst(node, applyImplicitG);
        case MisconceptionCode.WeakU:
            return applyTilFirst(node , applyWeakU);

    
        case MisconceptionCode.OtherImplicit: 
            // Apply known underconstrains or implicit underconstraints
            let res = applyTilFirst(node, applyImplicitPrefix);
            // If we can't find any, apply a general underconstraint
            if (!res.misconception) {
                return applyTilFirst(node, applyUnderconstraint);
            }

        case MisconceptionCode.BadProp: // This is the equiv of a syntax error right?   Could we apply a syntax error?


        case MisconceptionCode.Unlabeled:
        case MisconceptionCode.ReasonableVariant:
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

    if (node instanceof BinaryOperatorNode && node.operator == "U") {
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

// Just remove a G operator
function applyImplicitG(node : LTLNode) : MutationResult {

    if (node instanceof UnaryOperatorNode && node.operator == "G") {
        return new MutationResult(node.operand, MisconceptionCode.ImplicitG);
    }
    return new MutationResult(node);
}

// Just remove a F operator
function applyImplicitF(node : LTLNode) : MutationResult {

    if (node instanceof UnaryOperatorNode && node.operator == "F") {
        return new MutationResult(node.operand, MisconceptionCode.ImplicitF);
    }
    return new MutationResult(node);
}



function applyImplicitPrefix(node : LTLNode) : MutationResult {

    // THese are explicit examples from the codebook. Can we somehow generalize?
    if (node instanceof UntilNode) {
        
       let lhs = node.left;
       let rhs = node.right;

       // Find an instance of (not x) U x and replace it with F(x)
       if (lhs instanceof NotNode && LTLNode.equiv(lhs.operand, rhs)) {
               return new MutationResult(new FinallyNode(rhs), MisconceptionCode.OtherImplicit);
       }


       // Find an instance of x U G(not x) and replace it with x and F(G(not x))
         if (rhs instanceof GloballyNode && LTLNode.equiv(lhs, rhs.operand)) {
              return new MutationResult(new AndNode(lhs, new FinallyNode(rhs)), MisconceptionCode.OtherImplicit);
         }

    }

    // Find an instance of F(x) and G(x => X(G(not x))) and replace it with F(x and X(G(not x)))
    if (node instanceof AndNode) {
        let lhs = node.left;
        let rhs = node.right;

        if (lhs instanceof FinallyNode && rhs instanceof GloballyNode) {
            let rhs_operand = rhs.operand;
            if (rhs_operand instanceof ImpliesNode) {
                let rhs_operand_lhs = rhs_operand.left;
                let rhs_operand_rhs = rhs_operand.right;

                if (LTLNode.equiv(lhs.operand, rhs_operand_lhs) && rhs_operand_rhs instanceof NextNode && rhs_operand_rhs.operand instanceof GloballyNode && LTLNode.equiv(rhs_operand_lhs, rhs_operand_rhs.operand.operand)) {
                    return new MutationResult(new AndNode(lhs.operand, new NextNode(rhs)), MisconceptionCode.OtherImplicit);
                }
            }
        }
    }

    // Find an instance of X(x) and replace it with F(x)
    if (node instanceof NextNode) {
        return new MutationResult(new FinallyNode(node.operand), MisconceptionCode.OtherImplicit);
    }



   return new MutationResult(node);

}



// Is this what we want?
function applyUnderconstraint(node: LTLNode): MutationResult {





    // Check the type of the node
    if (node instanceof BinaryOperatorNode) {
        // If the node is a binary operator, remove one of its operands
        return new MutationResult(node.left, MisconceptionCode.OtherImplicit);
    } else if (node instanceof UnaryOperatorNode) {
        // If the node is a unary operator, remove the operator
        return new MutationResult(node.operand, MisconceptionCode.OtherImplicit);
    } else {
        // If the node is a proposition, return it as is
        return new MutationResult(node);
    }
}


function applyWeakU(node : LTLNode) : MutationResult {


    // Applies to responses that confuse the U operator with the weak variant W, which does not
    // guarantee that its second subterm eventually holds.
    // Expected x U y but subject wrote F(y) and x U y
    if (node instanceof UntilNode) {
        // Find an instance of x U y and replace it with x U y and F(y)
        let lhs = node.left;
        let rhs = node.right;

        let new_node = new AndNode(node, new FinallyNode(rhs));
        return new MutationResult(new_node, MisconceptionCode.WeakU);
    }

    return new MutationResult(node);
}


function applyBadStateQuantification(node: LTLNode): MutationResult {

    //  Applies to responses that mis-use or swap a fan-out operator (F, G, U).

    // If G is used, swap with F
    if (node instanceof GloballyNode) {
        let op = node.operand;
        return new MutationResult(new FinallyNode(op), MisconceptionCode.BadStateQuantification);
    }

    // If F is used, swap with G
    if (node instanceof FinallyNode) {
        let op = node.operand;
        return new MutationResult(new GloballyNode(op), MisconceptionCode.BadStateQuantification);
    }

    
    // TODO: Need more instances here
    if (node instanceof UntilNode) {
        let lhs = node.left;
        let rhs = node.right;

        // Generate a random number between 1 and 5
        let randomNum = Math.floor(Math.random() * 5) + 1;
        let new_node : LTLNode;

        switch (randomNum) {
            case 1:
                // If x U y, replace it with F(x) U y
                new_node = new UntilNode(new FinallyNode(lhs), rhs);
                break;
            case 2:
                // If x U y, replace it with G(x) U y
                new_node = new UntilNode(new GloballyNode(lhs), rhs);
                break;

            // This is subtle right? Does this overlap with other misconceptions?
            case 3:
                // If x U y, replace it with x U F(y)
                new_node = new UntilNode(lhs, new FinallyNode(rhs));
                break;
            case 4:
                // If x U y, replace it with x U G(y)
                new_node = new UntilNode(lhs, new GloballyNode(rhs));
                break;

            default:
                // If x U y, replace it with y U x
                new_node = new UntilNode(rhs, lhs);
                break;
        }
        return new MutationResult(new_node, MisconceptionCode.BadStateQuantification);
    }

    return new MutationResult(node);

}

function applyBadStateIndex(node: LTLNode): MutationResult {

    // Applies to responses that use a correct term at an incorrect state index. Does not
    // apply when a fan-out operator (F, G, U) is missing or included erroneously.

    // TODO: Think of others, or a general pattern?

    if (node instanceof UntilNode) {
        let lhs = node.left;
        let rhs = node.right;

        // Replace x U (y and F(z)) with (x U y) and F(z)
        if (rhs instanceof AndNode && rhs.right instanceof FinallyNode) {
            let new_node = new AndNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace x U (y and G(z)) with (x U y) and G(z)
        if (rhs instanceof AndNode && rhs.right instanceof GloballyNode) {
            let new_node = new AndNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace x U (y or F(z)) with (x U y) or F(z)
        if (rhs instanceof OrNode && rhs.right instanceof FinallyNode) {
            let new_node = new OrNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace x U (y or G(z)) with (x U y) or G(z)
        if (rhs instanceof OrNode && rhs.right instanceof GloballyNode) {
            let new_node = new OrNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace x U (y => F(z)) with (x U y) => F(z)
        if (rhs instanceof ImpliesNode && rhs.right instanceof FinallyNode) {
            let new_node = new ImpliesNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace x U (y => G(z)) with (x U y) => G(z)
        if (rhs instanceof ImpliesNode && rhs.right instanceof GloballyNode) {
            let new_node = new ImpliesNode(new UntilNode(lhs, rhs.left), rhs.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }
    }

    
    if (node instanceof NextNode) {
        let op = node.operand;

        // Replace X(x and y) with X(x) and y
        if (op instanceof AndNode) {
            let new_node = new AndNode(new NextNode(op.left), op.right);
            return new MutationResult(new_node, MisconceptionCode.BadStateIndex);
        }

        // Replace X(X(X(...(x)) with X(x) 
        if (op instanceof NextNode) {

            let x = op.operand;
            while (x instanceof NextNode) {
                x = x.operand;
            }

            return new MutationResult(new NextNode(x), MisconceptionCode.BadStateIndex);
        }
    }
    

    return new MutationResult(node);
}