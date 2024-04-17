

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
            //return applyPrecedence(node);
        case MisconceptionCode.ReasonableVariant:
            //return applyReasonableVariant(node);
        case MisconceptionCode.BadProp:
            //return applyBadProp(node);
        case MisconceptionCode.BadStateIndex:
            //return applyBadStateIndex(node);
        case MisconceptionCode.BadStateQuantification:
            //return applyBadStateQuantification(node);
        case MisconceptionCode.ExclusiveU:
            //return applyExclusiveU(node);
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