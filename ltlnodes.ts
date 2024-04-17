// Description: This file contains the classes for the nodes of the LTL syntax tree.

class LTLNode {
    type : string;
    constructor(type) {
        this.type = type;
    }
}


class UnaryOperatorNode extends LTLNode {
    constructor(operator, operand) {
        super('UnaryOperator');
        this.operator = operator;
        this.operand = operand;
    }
}

class BinaryOperatorNode extends LTLNode {
    constructor(operator, left, right) {
        super('BinaryOperator');
        this.operator = operator;
        this.left = left;
        this.right = right;
    }
}
////////////////////////////////////////////

class LiteralNode extends LTLNode {
    constructor(value) {
        super('Literal');
        this.value = value;
    }
}

class UntilNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('U', left, right);
    }
}

class NextNode extends UnaryOperatorNode {
    constructor(operand) {
        super('X', operand);
    }
}

class GloballyNode extends UnaryOperatorNode {
    constructor(operand) {
        super('G', operand);
    }
}


class FinallyNode extends UnaryOperatorNode {
    constructor(operand) {
        super('F', operand);
    }
}

class OrNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('||', left, right);
    }
}

class AndNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('&&', left, right);
    }
}

class NotNode extends UnaryOperatorNode {
    constructor(operand) {
        super('!', operand);
    }
}

class ImpliesNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('=>', left, right);
    }
}

class EquivalenceNode extends BinaryOperatorNode {
    constructor(left, right) {
        super('<=>', left, right);
    }
}