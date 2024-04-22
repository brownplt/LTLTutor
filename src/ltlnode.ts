// Description: This file contains the classes for the nodes of the LTL syntax tree.

import { CharStreams, CommonTokenStream } from 'antlr4ts';
import { ltlParser, FormulaContext } from './ltlParser';
import { ltlLexer } from './ltlLexer';
import { ltlListener } from './ltlListener';
import { DisjunctionContext, ConjunctionContext, UntilContext, ImplicationContext, EquivalenceContext, XContext, FContext, GContext, NotContext, ParenthesesContext, LiteralContext, LtlContext, AtomicFormulaContext } from './ltlParser';
import { ParseTreeWalker } from 'antlr4ts/tree/ParseTreeWalker';
import { ParseTreeListener } from 'antlr4ts/tree/ParseTreeListener';
import { TerminalNode } from 'antlr4ts/tree';



const reservedKeywords = ['X', 'G', 'F', 'U', '||', '&&', '!', '=>', '<=>'];



export abstract class LTLNode {
    type: string;
    constructor(type) {
        this.type = type;
    }

    abstract toString(): string;

    static equiv(a: LTLNode, b: LTLNode): boolean {
        return a.toString() === b.toString();
    }
}



class ltlListenerImpl implements ltlListener, ParseTreeListener {

    visitTerminal?: (/*@NotNull*/ node: TerminalNode) => void;


    private stack: LTLNode[] = [];



    exitDisjunction(ctx: DisjunctionContext) {
        // Pop the right operand from the stack
        const right = this.stack.pop();

        // Pop the left operand from the stack
        const left = this.stack.pop();

        // Construct a new OrNode and push it onto the stack
        const orNode = new OrNode(left, right);
        this.stack.push(orNode);
    }


    /**
     * Exit a parse tree produced by the `conjunction`
     * labeled alternative in `ltlParser.formula`.
     * @param ctx the parse tree
     */
    exitConjunction(ctx: ConjunctionContext) {
        // Pop the right operand from the stack
        const right = this.stack.pop();

        // Pop the left operand from the stack
        const left = this.stack.pop();

        // Construct a new AndNode and push it onto the stack
        const andNode = new AndNode(left, right);
        this.stack.push(andNode);
    }


    exitUntil(ctx: UntilContext) {
        const right = this.stack.pop();
        const left = this.stack.pop();
        const untilNode = new UntilNode(left, right);
        this.stack.push(untilNode);
    }



    exitImplication(ctx: ImplicationContext) {
        const right = this.stack.pop();
        const left = this.stack.pop();

        const impliesNode = new ImpliesNode(left, right);
        this.stack.push(impliesNode);
    }


    exitEquivalence(ctx: EquivalenceContext) {
        const right = this.stack.pop();
        const left = this.stack.pop();

        const equivNode = new EquivalenceNode(left, right);
        this.stack.push(equivNode);
    }


    exitX(ctx: XContext) {
        const operand = this.stack.pop();
        const nextNode = new NextNode(operand);
        this.stack.push(nextNode);
    }



    exitF(ctx: FContext) {
        const operand = this.stack.pop();
        const finallyNode = new FinallyNode(operand);
        this.stack.push(finallyNode);
    }


    exitG(ctx: GContext) {
        const operand = this.stack.pop();
        const globallyNode = new GloballyNode(operand);
        this.stack.push(globallyNode);
    }


    exitNot(ctx: NotContext) {
        // Pop the operand from the stack
        const operand = this.stack.pop();

        // Construct a new NotNode and push it onto the stack
        const notNode = new NotNode(operand);
        this.stack.push(notNode);
    }



    exitParentheses(ctx: ParenthesesContext) {
        // Pop the formula from the stack
        const formula = this.stack.pop();

        // Push the formula back onto the stack
        this.stack.push(formula);
    }



    // exitLiteral (ctx: LiteralContext) {
    //     // Get the literal value from the context
    //     const value = ctx.getText();

    //     // Construct a new LiteralNode and push it onto the stack
    //     const literalNode = new LiteralNode(value);
    //     this.stack.push(literalNode);
    // }

    exitAtomicFormula(ctx: AtomicFormulaContext) {
        // Get the atomic formula value from the context
        const value = ctx.ID().text;

        // Construct a new LiteralNode (or AtomicFormulaNode) and push it onto the stack
        const literalNode = new LiteralNode(value);
        this.stack.push(literalNode);
    }


    getRoot(): LTLNode {
        // Return the root of the tree (the last node on the stack)
        return this.stack[this.stack.length - 1];
    }
}



export class UnaryOperatorNode extends LTLNode {

    operator: string;
    operand: LTLNode;

    constructor(operator: string, operand: LTLNode) {
        super('UnaryOperator');
        this.operator = operator;
        this.operand = operand;
    }

    toString(): string {
        return `${this.operator}(${this.operand.toString()})`;
    }

}

export class BinaryOperatorNode extends LTLNode {

    operator: string;
    left: LTLNode;
    right: LTLNode;

    constructor(operator, left, right) {
        super('BinaryOperator');
        this.operator = operator;
        this.left = left;
        this.right = right;
    }

    toString(): string {
        return `(${this.left.toString()} ${this.operator} ${this.right.toString()})`;
    }
}
////////////////////////////////////////////

export class LiteralNode extends LTLNode {
    value: string;
    constructor(value) {
        super('Literal');
        this.value = value;
    }

    toString(): string {
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




function parseLTLString(s: string): LTLNode {
    const inputStream = CharStreams.fromString(s);
    const lexer = new ltlLexer(inputStream);
    const tokenStream = new CommonTokenStream(lexer);

    // Create the parser and parse the input
    const parser = new ltlParser(tokenStream);
    const tree = parser.ltl();
    const listener = new ltlListenerImpl();

    // Create a ParseTreeWalker
    const walker = new ParseTreeWalker();

    // Walk the parse tree with the listener
    walker.walk(listener, tree);


    const root = listener.getRoot();
    return root;
}

