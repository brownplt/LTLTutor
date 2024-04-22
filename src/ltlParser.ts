// Generated from ltl.g4 by ANTLR 4.9.0-SNAPSHOT


import { ATN } from "antlr4ts/atn/ATN";
import { ATNDeserializer } from "antlr4ts/atn/ATNDeserializer";
import { FailedPredicateException } from "antlr4ts/FailedPredicateException";
import { NotNull } from "antlr4ts/Decorators";
import { NoViableAltException } from "antlr4ts/NoViableAltException";
import { Override } from "antlr4ts/Decorators";
import { Parser } from "antlr4ts/Parser";
import { ParserRuleContext } from "antlr4ts/ParserRuleContext";
import { ParserATNSimulator } from "antlr4ts/atn/ParserATNSimulator";
import { ParseTreeListener } from "antlr4ts/tree/ParseTreeListener";
import { ParseTreeVisitor } from "antlr4ts/tree/ParseTreeVisitor";
import { RecognitionException } from "antlr4ts/RecognitionException";
import { RuleContext } from "antlr4ts/RuleContext";
//import { RuleVersion } from "antlr4ts/RuleVersion";
import { TerminalNode } from "antlr4ts/tree/TerminalNode";
import { Token } from "antlr4ts/Token";
import { TokenStream } from "antlr4ts/TokenStream";
import { Vocabulary } from "antlr4ts/Vocabulary";
import { VocabularyImpl } from "antlr4ts/VocabularyImpl";

import * as Utils from "antlr4ts/misc/Utils";

import { ltlListener } from "./ltlListener";

export class ltlParser extends Parser {
	public static readonly T__0 = 1;
	public static readonly T__1 = 2;
	public static readonly T__2 = 3;
	public static readonly T__3 = 4;
	public static readonly T__4 = 5;
	public static readonly T__5 = 6;
	public static readonly T__6 = 7;
	public static readonly T__7 = 8;
	public static readonly T__8 = 9;
	public static readonly T__9 = 10;
	public static readonly T__10 = 11;
	public static readonly ID = 12;
	public static readonly RULE_ltl = 0;
	public static readonly RULE_formula = 1;
	public static readonly RULE_atomicFormula = 2;
	// tslint:disable:no-trailing-whitespace
	public static readonly ruleNames: string[] = [
		"ltl", "formula", "atomicFormula",
	];

	private static readonly _LITERAL_NAMES: Array<string | undefined> = [
		undefined, "'||'", "'&&'", "'U'", "'=>'", "'<=>'", "'X'", "'F'", "'G'", 
		"'!'", "'('", "')'",
	];
	private static readonly _SYMBOLIC_NAMES: Array<string | undefined> = [
		undefined, undefined, undefined, undefined, undefined, undefined, undefined, 
		undefined, undefined, undefined, undefined, undefined, "ID",
	];
	public static readonly VOCABULARY: Vocabulary = new VocabularyImpl(ltlParser._LITERAL_NAMES, ltlParser._SYMBOLIC_NAMES, []);

	// @Override
	// @NotNull
	public get vocabulary(): Vocabulary {
		return ltlParser.VOCABULARY;
	}
	// tslint:enable:no-trailing-whitespace

	// @Override
	public get grammarFileName(): string { return "ltl.g4"; }

	// @Override
	public get ruleNames(): string[] { return ltlParser.ruleNames; }

	// @Override
	public get serializedATN(): string { return ltlParser._serializedATN; }

	protected createFailedPredicateException(predicate?: string, message?: string): FailedPredicateException {
		return new FailedPredicateException(this, predicate, message);
	}

	constructor(input: TokenStream) {
		super(input);
		this._interp = new ParserATNSimulator(ltlParser._ATN, this);
	}
	// @RuleVersion(0)
	public ltl(): LtlContext {
		let _localctx: LtlContext = new LtlContext(this._ctx, this.state);
		this.enterRule(_localctx, 0, ltlParser.RULE_ltl);
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 6;
			this.formula(0);
			this.state = 7;
			this.match(ltlParser.EOF);
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}

	public formula(): FormulaContext;
	public formula(_p: number): FormulaContext;
	// @RuleVersion(0)
	public formula(_p?: number): FormulaContext {
		if (_p === undefined) {
			_p = 0;
		}

		let _parentctx: ParserRuleContext = this._ctx;
		let _parentState: number = this.state;
		let _localctx: FormulaContext = new FormulaContext(this._ctx, _parentState);
		let _prevctx: FormulaContext = _localctx;
		let _startState: number = 2;
		this.enterRecursionRule(_localctx, 2, ltlParser.RULE_formula, _p);
		try {
			let _alt: number;
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 23;
			this._errHandler.sync(this);
			switch (this._input.LA(1)) {
			case ltlParser.T__5:
				{
				_localctx = new XContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;

				this.state = 10;
				this.match(ltlParser.T__5);
				this.state = 11;
				this.formula(6);
				}
				break;
			case ltlParser.T__6:
				{
				_localctx = new FContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;
				this.state = 12;
				this.match(ltlParser.T__6);
				this.state = 13;
				this.formula(5);
				}
				break;
			case ltlParser.T__7:
				{
				_localctx = new GContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;
				this.state = 14;
				this.match(ltlParser.T__7);
				this.state = 15;
				this.formula(4);
				}
				break;
			case ltlParser.T__8:
				{
				_localctx = new NotContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;
				this.state = 16;
				this.match(ltlParser.T__8);
				this.state = 17;
				this.formula(3);
				}
				break;
			case ltlParser.T__9:
				{
				_localctx = new ParenthesesContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;
				this.state = 18;
				this.match(ltlParser.T__9);
				this.state = 19;
				this.formula(0);
				this.state = 20;
				this.match(ltlParser.T__10);
				}
				break;
			case ltlParser.ID:
				{
				_localctx = new LiteralContext(_localctx);
				this._ctx = _localctx;
				_prevctx = _localctx;
				this.state = 22;
				this.atomicFormula();
				}
				break;
			default:
				throw new NoViableAltException(this);
			}
			this._ctx._stop = this._input.tryLT(-1);
			this.state = 42;
			this._errHandler.sync(this);
			_alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
			while (_alt !== 2 && _alt !== ATN.INVALID_ALT_NUMBER) {
				if (_alt === 1) {
					if (this._parseListeners != null) {
						this.triggerExitRuleEvent();
					}
					_prevctx = _localctx;
					{
					this.state = 40;
					this._errHandler.sync(this);
					switch ( this.interpreter.adaptivePredict(this._input, 1, this._ctx) ) {
					case 1:
						{
						_localctx = new DisjunctionContext(new FormulaContext(_parentctx, _parentState));
						this.pushNewRecursionContext(_localctx, _startState, ltlParser.RULE_formula);
						this.state = 25;
						if (!(this.precpred(this._ctx, 11))) {
							throw this.createFailedPredicateException("this.precpred(this._ctx, 11)");
						}
						this.state = 26;
						this.match(ltlParser.T__0);
						this.state = 27;
						this.formula(12);
						}
						break;

					case 2:
						{
						_localctx = new ConjunctionContext(new FormulaContext(_parentctx, _parentState));
						this.pushNewRecursionContext(_localctx, _startState, ltlParser.RULE_formula);
						this.state = 28;
						if (!(this.precpred(this._ctx, 10))) {
							throw this.createFailedPredicateException("this.precpred(this._ctx, 10)");
						}
						this.state = 29;
						this.match(ltlParser.T__1);
						this.state = 30;
						this.formula(11);
						}
						break;

					case 3:
						{
						_localctx = new UntilContext(new FormulaContext(_parentctx, _parentState));
						this.pushNewRecursionContext(_localctx, _startState, ltlParser.RULE_formula);
						this.state = 31;
						if (!(this.precpred(this._ctx, 9))) {
							throw this.createFailedPredicateException("this.precpred(this._ctx, 9)");
						}
						this.state = 32;
						this.match(ltlParser.T__2);
						this.state = 33;
						this.formula(10);
						}
						break;

					case 4:
						{
						_localctx = new ImplicationContext(new FormulaContext(_parentctx, _parentState));
						this.pushNewRecursionContext(_localctx, _startState, ltlParser.RULE_formula);
						this.state = 34;
						if (!(this.precpred(this._ctx, 8))) {
							throw this.createFailedPredicateException("this.precpred(this._ctx, 8)");
						}
						this.state = 35;
						this.match(ltlParser.T__3);
						this.state = 36;
						this.formula(9);
						}
						break;

					case 5:
						{
						_localctx = new EquivalenceContext(new FormulaContext(_parentctx, _parentState));
						this.pushNewRecursionContext(_localctx, _startState, ltlParser.RULE_formula);
						this.state = 37;
						if (!(this.precpred(this._ctx, 7))) {
							throw this.createFailedPredicateException("this.precpred(this._ctx, 7)");
						}
						this.state = 38;
						this.match(ltlParser.T__4);
						this.state = 39;
						this.formula(8);
						}
						break;
					}
					}
				}
				this.state = 44;
				this._errHandler.sync(this);
				_alt = this.interpreter.adaptivePredict(this._input, 2, this._ctx);
			}
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.unrollRecursionContexts(_parentctx);
		}
		return _localctx;
	}
	// @RuleVersion(0)
	public atomicFormula(): AtomicFormulaContext {
		let _localctx: AtomicFormulaContext = new AtomicFormulaContext(this._ctx, this.state);
		this.enterRule(_localctx, 4, ltlParser.RULE_atomicFormula);
		try {
			this.enterOuterAlt(_localctx, 1);
			{
			this.state = 45;
			this.match(ltlParser.ID);
			}
		}
		catch (re) {
			if (re instanceof RecognitionException) {
				_localctx.exception = re;
				this._errHandler.reportError(this, re);
				this._errHandler.recover(this, re);
			} else {
				throw re;
			}
		}
		finally {
			this.exitRule();
		}
		return _localctx;
	}

	public sempred(_localctx: RuleContext, ruleIndex: number, predIndex: number): boolean {
		switch (ruleIndex) {
		case 1:
			return this.formula_sempred(_localctx as FormulaContext, predIndex);
		}
		return true;
	}
	private formula_sempred(_localctx: FormulaContext, predIndex: number): boolean {
		switch (predIndex) {
		case 0:
			return this.precpred(this._ctx, 11);

		case 1:
			return this.precpred(this._ctx, 10);

		case 2:
			return this.precpred(this._ctx, 9);

		case 3:
			return this.precpred(this._ctx, 8);

		case 4:
			return this.precpred(this._ctx, 7);
		}
		return true;
	}

	public static readonly _serializedATN: string =
		"\x03\uC91D\uCABA\u058D\uAFBA\u4F53\u0607\uEA8B\uC241\x03\x0E2\x04\x02" +
		"\t\x02\x04\x03\t\x03\x04\x04\t\x04\x03\x02\x03\x02\x03\x02\x03\x03\x03" +
		"\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03" +
		"\x03\x03\x03\x03\x03\x03\x03\x05\x03\x1A\n\x03\x03\x03\x03\x03\x03\x03" +
		"\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03\x03" +
		"\x03\x03\x03\x03\x03\x03\x07\x03+\n\x03\f\x03\x0E\x03.\v\x03\x03\x04\x03" +
		"\x04\x03\x04\x02\x02\x03\x04\x05\x02\x02\x04\x02\x06\x02\x02\x02\x028" +
		"\x02\b\x03\x02\x02\x02\x04\x19\x03\x02\x02\x02\x06/\x03\x02\x02\x02\b" +
		"\t\x05\x04\x03\x02\t\n\x07\x02\x02\x03\n\x03\x03\x02\x02\x02\v\f\b\x03" +
		"\x01\x02\f\r\x07\b\x02\x02\r\x1A\x05\x04\x03\b\x0E\x0F\x07\t\x02\x02\x0F" +
		"\x1A\x05\x04\x03\x07\x10\x11\x07\n\x02\x02\x11\x1A\x05\x04\x03\x06\x12" +
		"\x13\x07\v\x02\x02\x13\x1A\x05\x04\x03\x05\x14\x15\x07\f\x02\x02\x15\x16" +
		"\x05\x04\x03\x02\x16\x17\x07\r\x02\x02\x17\x1A\x03\x02\x02\x02\x18\x1A" +
		"\x05\x06\x04\x02\x19\v\x03\x02\x02\x02\x19\x0E\x03\x02\x02\x02\x19\x10" +
		"\x03\x02\x02\x02\x19\x12\x03\x02\x02\x02\x19\x14\x03\x02\x02\x02\x19\x18" +
		"\x03\x02\x02\x02\x1A,\x03\x02\x02\x02\x1B\x1C\f\r\x02\x02\x1C\x1D\x07" +
		"\x03\x02\x02\x1D+\x05\x04\x03\x0E\x1E\x1F\f\f\x02\x02\x1F \x07\x04\x02" +
		"\x02 +\x05\x04\x03\r!\"\f\v\x02\x02\"#\x07\x05\x02\x02#+\x05\x04\x03\f" +
		"$%\f\n\x02\x02%&\x07\x06\x02\x02&+\x05\x04\x03\v\'(\f\t\x02\x02()\x07" +
		"\x07\x02\x02)+\x05\x04\x03\n*\x1B\x03\x02\x02\x02*\x1E\x03\x02\x02\x02" +
		"*!\x03\x02\x02\x02*$\x03\x02\x02\x02*\'\x03\x02\x02\x02+.\x03\x02\x02" +
		"\x02,*\x03\x02\x02\x02,-\x03\x02\x02\x02-\x05\x03\x02\x02\x02.,\x03\x02" +
		"\x02\x02/0\x07\x0E\x02\x020\x07\x03\x02\x02\x02\x05\x19*,";
	public static __ATN: ATN;
	public static get _ATN(): ATN {
		if (!ltlParser.__ATN) {
			ltlParser.__ATN = new ATNDeserializer().deserialize(Utils.toCharArray(ltlParser._serializedATN));
		}

		return ltlParser.__ATN;
	}

}

export class LtlContext extends ParserRuleContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	public EOF(): TerminalNode { return this.getToken(ltlParser.EOF, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return ltlParser.RULE_ltl; }
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterLtl) {
			listener.enterLtl(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitLtl) {
			listener.exitLtl(this);
		}
	}
}


export class FormulaContext extends ParserRuleContext {
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return ltlParser.RULE_formula; }
	public copyFrom(ctx: FormulaContext): void {
		super.copyFrom(ctx);
	}
}
export class DisjunctionContext extends FormulaContext {
	public formula(): FormulaContext[];
	public formula(i: number): FormulaContext;
	public formula(i?: number): FormulaContext | FormulaContext[] {
		if (i === undefined) {
			return this.getRuleContexts(FormulaContext);
		} else {
			return this.getRuleContext(i, FormulaContext);
		}
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterDisjunction) {
			listener.enterDisjunction(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitDisjunction) {
			listener.exitDisjunction(this);
		}
	}
}
export class ConjunctionContext extends FormulaContext {
	public formula(): FormulaContext[];
	public formula(i: number): FormulaContext;
	public formula(i?: number): FormulaContext | FormulaContext[] {
		if (i === undefined) {
			return this.getRuleContexts(FormulaContext);
		} else {
			return this.getRuleContext(i, FormulaContext);
		}
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterConjunction) {
			listener.enterConjunction(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitConjunction) {
			listener.exitConjunction(this);
		}
	}
}
export class UntilContext extends FormulaContext {
	public formula(): FormulaContext[];
	public formula(i: number): FormulaContext;
	public formula(i?: number): FormulaContext | FormulaContext[] {
		if (i === undefined) {
			return this.getRuleContexts(FormulaContext);
		} else {
			return this.getRuleContext(i, FormulaContext);
		}
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterUntil) {
			listener.enterUntil(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitUntil) {
			listener.exitUntil(this);
		}
	}
}
export class ImplicationContext extends FormulaContext {
	public formula(): FormulaContext[];
	public formula(i: number): FormulaContext;
	public formula(i?: number): FormulaContext | FormulaContext[] {
		if (i === undefined) {
			return this.getRuleContexts(FormulaContext);
		} else {
			return this.getRuleContext(i, FormulaContext);
		}
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterImplication) {
			listener.enterImplication(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitImplication) {
			listener.exitImplication(this);
		}
	}
}
export class EquivalenceContext extends FormulaContext {
	public formula(): FormulaContext[];
	public formula(i: number): FormulaContext;
	public formula(i?: number): FormulaContext | FormulaContext[] {
		if (i === undefined) {
			return this.getRuleContexts(FormulaContext);
		} else {
			return this.getRuleContext(i, FormulaContext);
		}
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterEquivalence) {
			listener.enterEquivalence(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitEquivalence) {
			listener.exitEquivalence(this);
		}
	}
}
export class XContext extends FormulaContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterX) {
			listener.enterX(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitX) {
			listener.exitX(this);
		}
	}
}
export class FContext extends FormulaContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterF) {
			listener.enterF(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitF) {
			listener.exitF(this);
		}
	}
}
export class GContext extends FormulaContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterG) {
			listener.enterG(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitG) {
			listener.exitG(this);
		}
	}
}
export class NotContext extends FormulaContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterNot) {
			listener.enterNot(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitNot) {
			listener.exitNot(this);
		}
	}
}
export class ParenthesesContext extends FormulaContext {
	public formula(): FormulaContext {
		return this.getRuleContext(0, FormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterParentheses) {
			listener.enterParentheses(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitParentheses) {
			listener.exitParentheses(this);
		}
	}
}
export class LiteralContext extends FormulaContext {
	public atomicFormula(): AtomicFormulaContext {
		return this.getRuleContext(0, AtomicFormulaContext);
	}
	constructor(ctx: FormulaContext) {
		super(ctx.parent, ctx.invokingState);
		this.copyFrom(ctx);
	}
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterLiteral) {
			listener.enterLiteral(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitLiteral) {
			listener.exitLiteral(this);
		}
	}
}


export class AtomicFormulaContext extends ParserRuleContext {
	public ID(): TerminalNode { return this.getToken(ltlParser.ID, 0); }
	constructor(parent: ParserRuleContext | undefined, invokingState: number) {
		super(parent, invokingState);
	}
	// @Override
	public get ruleIndex(): number { return ltlParser.RULE_atomicFormula; }
	// @Override
	public enterRule(listener: ltlListener): void {
		if (listener.enterAtomicFormula) {
			listener.enterAtomicFormula(this);
		}
	}
	// @Override
	public exitRule(listener: ltlListener): void {
		if (listener.exitAtomicFormula) {
			listener.exitAtomicFormula(this);
		}
	}
}


