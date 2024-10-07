# Generated from ltl.g4 by ANTLR 4.9.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3\24")
        buf.write("\62\4\2\t\2\4\3\t\3\4\4\t\4\3\2\3\2\3\2\3\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\5\3\32\n\3")
        buf.write("\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3\3")
        buf.write("\3\3\3\7\3+\n\3\f\3\16\3.\13\3\3\4\3\4\3\4\2\3\4\5\2\4")
        buf.write("\6\2\6\3\2\t\13\3\2\f\r\3\2\16\17\3\2\5\6\28\2\b\3\2\2")
        buf.write("\2\4\31\3\2\2\2\6/\3\2\2\2\b\t\5\4\3\2\t\n\7\2\2\3\n\3")
        buf.write("\3\2\2\2\13\f\b\3\1\2\f\r\t\2\2\2\r\32\5\4\3\b\16\17\t")
        buf.write("\3\2\2\17\32\5\4\3\7\20\21\t\4\2\2\21\32\5\4\3\6\22\23")
        buf.write("\7\20\2\2\23\32\5\4\3\5\24\25\7\21\2\2\25\26\5\4\3\2\26")
        buf.write("\27\7\22\2\2\27\32\3\2\2\2\30\32\5\6\4\2\31\13\3\2\2\2")
        buf.write("\31\16\3\2\2\2\31\20\3\2\2\2\31\22\3\2\2\2\31\24\3\2\2")
        buf.write("\2\31\30\3\2\2\2\32,\3\2\2\2\33\34\f\r\2\2\34\35\7\3\2")
        buf.write("\2\35+\5\4\3\16\36\37\f\f\2\2\37 \7\4\2\2 +\5\4\3\r!\"")
        buf.write("\f\13\2\2\"#\t\5\2\2#+\5\4\3\f$%\f\n\2\2%&\7\7\2\2&+\5")
        buf.write("\4\3\13\'(\f\t\2\2()\7\b\2\2)+\5\4\3\n*\33\3\2\2\2*\36")
        buf.write("\3\2\2\2*!\3\2\2\2*$\3\2\2\2*\'\3\2\2\2+.\3\2\2\2,*\3")
        buf.write("\2\2\2,-\3\2\2\2-\5\3\2\2\2.,\3\2\2\2/\60\7\23\2\2\60")
        buf.write("\7\3\2\2\2\5\31*,")
        return buf.getvalue()


class ltlParser ( Parser ):

    grammarFileName = "ltl.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'|'", "'&'", "'U'", "'UNTIL'", "'->'", 
                     "'<->'", "'X'", "'NEXT'", "'NEXT_STATE'", "'F'", "'EVENTUALLY'", 
                     "'G'", "'ALWAYS'", "'!'", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "ID", "WS" ]

    RULE_ltl = 0
    RULE_formula = 1
    RULE_atomicFormula = 2

    ruleNames =  [ "ltl", "formula", "atomicFormula" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    T__10=11
    T__11=12
    T__12=13
    T__13=14
    T__14=15
    T__15=16
    ID=17
    WS=18

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.9.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None



    class LtlContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def EOF(self):
            return self.getToken(ltlParser.EOF, 0)

        def getRuleIndex(self):
            return ltlParser.RULE_ltl

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLtl" ):
                listener.enterLtl(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLtl" ):
                listener.exitLtl(self)




    def ltl(self):

        localctx = ltlParser.LtlContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_ltl)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 6
            self.formula(0)
            self.state = 7
            self.match(ltlParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx

    class FormulaContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return ltlParser.RULE_formula

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class NextContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNext" ):
                listener.enterNext(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNext" ):
                listener.exitNext(self)


    class AlwaysContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAlways" ):
                listener.enterAlways(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAlways" ):
                listener.exitAlways(self)


    class ParenthesesContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParentheses" ):
                listener.enterParentheses(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParentheses" ):
                listener.exitParentheses(self)


    class NotContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNot" ):
                listener.enterNot(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNot" ):
                listener.exitNot(self)


    class EquivalenceContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEquivalence" ):
                listener.enterEquivalence(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEquivalence" ):
                listener.exitEquivalence(self)


    class ConjunctionContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConjunction" ):
                listener.enterConjunction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConjunction" ):
                listener.exitConjunction(self)


    class DisjunctionContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDisjunction" ):
                listener.enterDisjunction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDisjunction" ):
                listener.exitDisjunction(self)


    class ImplicationContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterImplication" ):
                listener.enterImplication(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitImplication" ):
                listener.exitImplication(self)


    class EventuallyContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEventually" ):
                listener.enterEventually(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEventually" ):
                listener.exitEventually(self)


    class UntilContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterUntil" ):
                listener.enterUntil(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitUntil" ):
                listener.exitUntil(self)


    class LiteralContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def atomicFormula(self):
            return self.getTypedRuleContext(ltlParser.AtomicFormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterLiteral" ):
                listener.enterLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitLiteral" ):
                listener.exitLiteral(self)



    def formula(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = ltlParser.FormulaContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 2
        self.enterRecursionRule(localctx, 2, self.RULE_formula, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 23
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [ltlParser.T__6, ltlParser.T__7, ltlParser.T__8]:
                localctx = ltlParser.NextContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 10
                _la = self._input.LA(1)
                if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << ltlParser.T__6) | (1 << ltlParser.T__7) | (1 << ltlParser.T__8))) != 0)):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 11
                self.formula(6)
                pass
            elif token in [ltlParser.T__9, ltlParser.T__10]:
                localctx = ltlParser.EventuallyContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 12
                _la = self._input.LA(1)
                if not(_la==ltlParser.T__9 or _la==ltlParser.T__10):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 13
                self.formula(5)
                pass
            elif token in [ltlParser.T__11, ltlParser.T__12]:
                localctx = ltlParser.AlwaysContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 14
                _la = self._input.LA(1)
                if not(_la==ltlParser.T__11 or _la==ltlParser.T__12):
                    self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 15
                self.formula(4)
                pass
            elif token in [ltlParser.T__13]:
                localctx = ltlParser.NotContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 16
                self.match(ltlParser.T__13)
                self.state = 17
                self.formula(3)
                pass
            elif token in [ltlParser.T__14]:
                localctx = ltlParser.ParenthesesContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 18
                self.match(ltlParser.T__14)
                self.state = 19
                self.formula(0)
                self.state = 20
                self.match(ltlParser.T__15)
                pass
            elif token in [ltlParser.ID]:
                localctx = ltlParser.LiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 22
                self.atomicFormula()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 42
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 40
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
                    if la_ == 1:
                        localctx = ltlParser.DisjunctionContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 25
                        if not self.precpred(self._ctx, 11):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 11)")
                        self.state = 26
                        self.match(ltlParser.T__0)
                        self.state = 27
                        self.formula(12)
                        pass

                    elif la_ == 2:
                        localctx = ltlParser.ConjunctionContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 28
                        if not self.precpred(self._ctx, 10):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 10)")
                        self.state = 29
                        self.match(ltlParser.T__1)
                        self.state = 30
                        self.formula(11)
                        pass

                    elif la_ == 3:
                        localctx = ltlParser.UntilContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 31
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 32
                        _la = self._input.LA(1)
                        if not(_la==ltlParser.T__2 or _la==ltlParser.T__3):
                            self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 33
                        self.formula(10)
                        pass

                    elif la_ == 4:
                        localctx = ltlParser.ImplicationContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 34
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 35
                        self.match(ltlParser.T__4)
                        self.state = 36
                        self.formula(9)
                        pass

                    elif la_ == 5:
                        localctx = ltlParser.EquivalenceContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 37
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 38
                        self.match(ltlParser.T__5)
                        self.state = 39
                        self.formula(8)
                        pass

             
                self.state = 44
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx

    class AtomicFormulaContext(ParserRuleContext):
        __slots__ = 'parser'

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ID(self):
            return self.getToken(ltlParser.ID, 0)

        def getRuleIndex(self):
            return ltlParser.RULE_atomicFormula

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAtomicFormula" ):
                listener.enterAtomicFormula(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAtomicFormula" ):
                listener.exitAtomicFormula(self)




    def atomicFormula(self):

        localctx = ltlParser.AtomicFormulaContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_atomicFormula)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 45
            self.match(ltlParser.ID)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[1] = self.formula_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def formula_sempred(self, localctx:FormulaContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 11)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 10)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 7)
         




