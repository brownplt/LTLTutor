// Description: This file contains the classes for the nodes of the LTL syntax tree.

export abstract class LTLNode {
    type : string;
    constructor(type) {
        this.type = type;
    }

    abstract toString() : string;



    static equiv(a : LTLNode, b : LTLNode) : boolean {
        return a.toString() === b.toString();
    }
}


export class UnaryOperatorNode extends LTLNode {

    operator : string;
    operand : LTLNode;

    constructor(operator : string, operand : LTLNode) {
        super('UnaryOperator');
        this.operator = operator;
        this.operand = operand;
    }

    toString() : string {
        return `${this.operator}(${this.operand.toString()})`;
    }

}

export class BinaryOperatorNode extends LTLNode {

    operator : string;
    left : LTLNode;
    right : LTLNode;

    constructor(operator, left, right) {
        super('BinaryOperator');
        this.operator = operator;
        this.left = left;
        this.right = right;
    }

    toString() : string {
        return `(${this.left.toString()} ${this.operator} ${this.right.toString()})`;
    }
}
////////////////////////////////////////////

export class LiteralNode extends LTLNode {
    value : string;
    constructor(value) {
        super('Literal');
        this.value = value;
    }

    toString() : string {
        return this.value;
    }
}

export class UntilNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('U', left, right);
    }
}

export class NextNode extends UnaryOperatorNode {
    constructor(operand) {
        super('X', operand);
    }
}

export class GloballyNode extends UnaryOperatorNode {
    constructor(operand) {
        super('G', operand);
    }
}


export class FinallyNode extends UnaryOperatorNode {
    constructor(operand) {
        super('F', operand);
    }
}

export class OrNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('||', left, right);
    }
}

export class AndNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('&&', left, right);
    }
}

export class NotNode extends UnaryOperatorNode {
    constructor(operand) {
        super('!', operand);
    }
}

export class ImpliesNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('=>', left, right);
    }
}

export class EquivalenceNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('<=>', left, right);
    }
}

export default LTLNode;


function normalizeNode(node: LTLNode): LTLNode {

    if (node instanceof UnaryOperatorNode) {
        const operand = normalizeNode(node.operand);
        return new UnaryOperatorNode(node.operator, operand);
    } else if (node instanceof BinaryOperatorNode) {

        // If an operator is a binary operator, we have to determine a cannonical order for left and right.
        // This is the case for ^, or, , <=>
        // But not => or Until


        // But also, normalizing doesn't matter that much right?

        const left = normalizeNode(node.left);
        const right = normalizeNode(node.right);
        return new BinaryOperatorNode(node.operator, left, right);
    } else {
        return node;
    }
}

