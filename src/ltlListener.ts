// Generated from ltl.g4 by ANTLR 4.9.0-SNAPSHOT


import { ParseTreeListener } from "antlr4ts/tree/ParseTreeListener";

import { DisjunctionContext } from "./ltlParser";
import { ConjunctionContext } from "./ltlParser";
import { UntilContext } from "./ltlParser";
import { ImplicationContext } from "./ltlParser";
import { EquivalenceContext } from "./ltlParser";
import { XContext } from "./ltlParser";
import { FContext } from "./ltlParser";
import { GContext } from "./ltlParser";
import { NotContext } from "./ltlParser";
import { ParenthesesContext } from "./ltlParser";
import { LiteralContext } from "./ltlParser";
import { LtlContext } from "./ltlParser";
import { FormulaContext } from "./ltlParser";
import { AtomicFormulaContext } from "./ltlParser";


/**
 * This interface defines a complete listener for a parse tree produced by
 * `ltlParser`.
 */
export interface ltlListener extends ParseTreeListener {
	/**
	 * Enter a parse tree produced by the `disjunction`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterDisjunction?: (ctx: DisjunctionContext) => void;
	/**
	 * Exit a parse tree produced by the `disjunction`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitDisjunction?: (ctx: DisjunctionContext) => void;

	/**
	 * Enter a parse tree produced by the `conjunction`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterConjunction?: (ctx: ConjunctionContext) => void;
	/**
	 * Exit a parse tree produced by the `conjunction`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitConjunction?: (ctx: ConjunctionContext) => void;

	/**
	 * Enter a parse tree produced by the `until`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterUntil?: (ctx: UntilContext) => void;
	/**
	 * Exit a parse tree produced by the `until`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitUntil?: (ctx: UntilContext) => void;

	/**
	 * Enter a parse tree produced by the `implication`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterImplication?: (ctx: ImplicationContext) => void;
	/**
	 * Exit a parse tree produced by the `implication`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitImplication?: (ctx: ImplicationContext) => void;

	/**
	 * Enter a parse tree produced by the `equivalence`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterEquivalence?: (ctx: EquivalenceContext) => void;
	/**
	 * Exit a parse tree produced by the `equivalence`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitEquivalence?: (ctx: EquivalenceContext) => void;

	/**
	 * Enter a parse tree produced by the `X`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterX?: (ctx: XContext) => void;
	/**
	 * Exit a parse tree produced by the `X`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitX?: (ctx: XContext) => void;

	/**
	 * Enter a parse tree produced by the `F`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterF?: (ctx: FContext) => void;
	/**
	 * Exit a parse tree produced by the `F`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitF?: (ctx: FContext) => void;

	/**
	 * Enter a parse tree produced by the `G`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterG?: (ctx: GContext) => void;
	/**
	 * Exit a parse tree produced by the `G`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitG?: (ctx: GContext) => void;

	/**
	 * Enter a parse tree produced by the `not`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterNot?: (ctx: NotContext) => void;
	/**
	 * Exit a parse tree produced by the `not`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitNot?: (ctx: NotContext) => void;

	/**
	 * Enter a parse tree produced by the `parentheses`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterParentheses?: (ctx: ParenthesesContext) => void;
	/**
	 * Exit a parse tree produced by the `parentheses`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitParentheses?: (ctx: ParenthesesContext) => void;

	/**
	 * Enter a parse tree produced by the `literal`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterLiteral?: (ctx: LiteralContext) => void;
	/**
	 * Exit a parse tree produced by the `literal`
	 * labeled alternative in `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitLiteral?: (ctx: LiteralContext) => void;

	/**
	 * Enter a parse tree produced by `ltlParser.ltl`.
	 * @param ctx the parse tree
	 */
	enterLtl?: (ctx: LtlContext) => void;
	/**
	 * Exit a parse tree produced by `ltlParser.ltl`.
	 * @param ctx the parse tree
	 */
	exitLtl?: (ctx: LtlContext) => void;

	/**
	 * Enter a parse tree produced by `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	enterFormula?: (ctx: FormulaContext) => void;
	/**
	 * Exit a parse tree produced by `ltlParser.formula`.
	 * @param ctx the parse tree
	 */
	exitFormula?: (ctx: FormulaContext) => void;

	/**
	 * Enter a parse tree produced by `ltlParser.atomicFormula`.
	 * @param ctx the parse tree
	 */
	enterAtomicFormula?: (ctx: AtomicFormulaContext) => void;
	/**
	 * Exit a parse tree produced by `ltlParser.atomicFormula`.
	 * @param ctx the parse tree
	 */
	exitAtomicFormula?: (ctx: AtomicFormulaContext) => void;
}

