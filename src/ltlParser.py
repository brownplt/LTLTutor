# Generated from ltl.g4 by ANTLR 4.13.1
# encoding: utf-8
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
	from typing import TextIO
else:
	from typing.io import TextIO

def serializedATN():
    return [
        4,1,12,44,2,0,7,0,2,1,7,1,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,22,8,1,1,1,1,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,5,1,39,8,1,10,1,12,1,42,9,1,
        1,1,0,1,2,2,0,2,0,0,51,0,4,1,0,0,0,2,21,1,0,0,0,4,5,3,2,1,0,5,6,
        5,0,0,1,6,1,1,0,0,0,7,8,6,1,-1,0,8,9,5,3,0,0,9,22,3,2,1,6,10,11,
        5,4,0,0,11,22,3,2,1,5,12,13,5,5,0,0,13,22,3,2,1,4,14,15,5,6,0,0,
        15,22,3,2,1,3,16,17,5,1,0,0,17,18,3,2,1,0,18,19,5,2,0,0,19,22,1,
        0,0,0,20,22,5,12,0,0,21,7,1,0,0,0,21,10,1,0,0,0,21,12,1,0,0,0,21,
        14,1,0,0,0,21,16,1,0,0,0,21,20,1,0,0,0,22,40,1,0,0,0,23,24,10,11,
        0,0,24,25,5,7,0,0,25,39,3,2,1,12,26,27,10,10,0,0,27,28,5,8,0,0,28,
        39,3,2,1,11,29,30,10,9,0,0,30,31,5,9,0,0,31,39,3,2,1,10,32,33,10,
        8,0,0,33,34,5,10,0,0,34,39,3,2,1,9,35,36,10,7,0,0,36,37,5,11,0,0,
        37,39,3,2,1,8,38,23,1,0,0,0,38,26,1,0,0,0,38,29,1,0,0,0,38,32,1,
        0,0,0,38,35,1,0,0,0,39,42,1,0,0,0,40,38,1,0,0,0,40,41,1,0,0,0,41,
        3,1,0,0,0,42,40,1,0,0,0,3,21,38,40
    ]

class ltlParser ( Parser ):

    grammarFileName = "ltl.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'('", "')'", "'X'", "'F'", "'G'", "'!'", 
                     "'|'", "'&'", "'U'", "'->'", "'<->'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "X", "F", "G", 
                      "NOT", "OR", "AND", "U", "IMPLIES", "EQUIV", "ID" ]

    RULE_ltl = 0
    RULE_formula = 1

    ruleNames =  [ "ltl", "formula" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    X=3
    F=4
    G=5
    NOT=6
    OR=7
    AND=8
    U=9
    IMPLIES=10
    EQUIV=11
    ID=12

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.1")
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
            self.state = 4
            self.formula(0)
            self.state = 5
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

        def NOT(self):
            return self.getToken(ltlParser.NOT, 0)
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

        def EQUIV(self):
            return self.getToken(ltlParser.EQUIV, 0)

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

        def AND(self):
            return self.getToken(ltlParser.AND, 0)

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

        def OR(self):
            return self.getToken(ltlParser.OR, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterDisjunction" ):
                listener.enterDisjunction(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitDisjunction" ):
                listener.exitDisjunction(self)


    class FContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def F(self):
            return self.getToken(ltlParser.F, 0)
        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterF" ):
                listener.enterF(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitF" ):
                listener.exitF(self)


    class ImplicationContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)

        def IMPLIES(self):
            return self.getToken(ltlParser.IMPLIES, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterImplication" ):
                listener.enterImplication(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitImplication" ):
                listener.exitImplication(self)


    class GContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def G(self):
            return self.getToken(ltlParser.G, 0)
        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterG" ):
                listener.enterG(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitG" ):
                listener.exitG(self)


    class XContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def X(self):
            return self.getToken(ltlParser.X, 0)
        def formula(self):
            return self.getTypedRuleContext(ltlParser.FormulaContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterX" ):
                listener.enterX(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitX" ):
                listener.exitX(self)


    class UntilContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def formula(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(ltlParser.FormulaContext)
            else:
                return self.getTypedRuleContext(ltlParser.FormulaContext,i)

        def U(self):
            return self.getToken(ltlParser.U, 0)

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

        def ID(self):
            return self.getToken(ltlParser.ID, 0)

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
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 21
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [3]:
                localctx = ltlParser.XContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 8
                self.match(ltlParser.X)
                self.state = 9
                self.formula(6)
                pass
            elif token in [4]:
                localctx = ltlParser.FContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 10
                self.match(ltlParser.F)
                self.state = 11
                self.formula(5)
                pass
            elif token in [5]:
                localctx = ltlParser.GContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 12
                self.match(ltlParser.G)
                self.state = 13
                self.formula(4)
                pass
            elif token in [6]:
                localctx = ltlParser.NotContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 14
                self.match(ltlParser.NOT)
                self.state = 15
                self.formula(3)
                pass
            elif token in [1]:
                localctx = ltlParser.ParenthesesContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 16
                self.match(ltlParser.T__0)
                self.state = 17
                self.formula(0)
                self.state = 18
                self.match(ltlParser.T__1)
                pass
            elif token in [12]:
                localctx = ltlParser.LiteralContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 20
                self.match(ltlParser.ID)
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 40
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,2,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 38
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,1,self._ctx)
                    if la_ == 1:
                        localctx = ltlParser.DisjunctionContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 23
                        if not self.precpred(self._ctx, 11):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 11)")
                        self.state = 24
                        self.match(ltlParser.OR)
                        self.state = 25
                        self.formula(12)
                        pass

                    elif la_ == 2:
                        localctx = ltlParser.ConjunctionContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 26
                        if not self.precpred(self._ctx, 10):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 10)")
                        self.state = 27
                        self.match(ltlParser.AND)
                        self.state = 28
                        self.formula(11)
                        pass

                    elif la_ == 3:
                        localctx = ltlParser.UntilContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 29
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 30
                        self.match(ltlParser.U)
                        self.state = 31
                        self.formula(10)
                        pass

                    elif la_ == 4:
                        localctx = ltlParser.ImplicationContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 32
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 33
                        self.match(ltlParser.IMPLIES)
                        self.state = 34
                        self.formula(9)
                        pass

                    elif la_ == 5:
                        localctx = ltlParser.EquivalenceContext(self, ltlParser.FormulaContext(self, _parentctx, _parentState))
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_formula)
                        self.state = 35
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 36
                        self.match(ltlParser.EQUIV)
                        self.state = 37
                        self.formula(8)
                        pass

             
                self.state = 42
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,2,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
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
         




