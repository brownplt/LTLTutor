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
        4,1,12,48,2,0,7,0,2,1,7,1,2,2,7,2,1,0,1,0,1,0,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,3,1,24,8,1,1,1,1,1,1,1,1,1,
        1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,5,1,41,8,1,10,1,12,1,
        44,9,1,1,2,1,2,1,2,0,1,2,3,0,2,4,0,0,54,0,6,1,0,0,0,2,23,1,0,0,0,
        4,45,1,0,0,0,6,7,3,2,1,0,7,8,5,0,0,1,8,1,1,0,0,0,9,10,6,1,-1,0,10,
        11,5,6,0,0,11,24,3,2,1,6,12,13,5,7,0,0,13,24,3,2,1,5,14,15,5,8,0,
        0,15,24,3,2,1,4,16,17,5,9,0,0,17,24,3,2,1,3,18,19,5,10,0,0,19,20,
        3,2,1,0,20,21,5,11,0,0,21,24,1,0,0,0,22,24,3,4,2,0,23,9,1,0,0,0,
        23,12,1,0,0,0,23,14,1,0,0,0,23,16,1,0,0,0,23,18,1,0,0,0,23,22,1,
        0,0,0,24,42,1,0,0,0,25,26,10,11,0,0,26,27,5,1,0,0,27,41,3,2,1,12,
        28,29,10,10,0,0,29,30,5,2,0,0,30,41,3,2,1,11,31,32,10,9,0,0,32,33,
        5,3,0,0,33,41,3,2,1,10,34,35,10,8,0,0,35,36,5,4,0,0,36,41,3,2,1,
        9,37,38,10,7,0,0,38,39,5,5,0,0,39,41,3,2,1,8,40,25,1,0,0,0,40,28,
        1,0,0,0,40,31,1,0,0,0,40,34,1,0,0,0,40,37,1,0,0,0,41,44,1,0,0,0,
        42,40,1,0,0,0,42,43,1,0,0,0,43,3,1,0,0,0,44,42,1,0,0,0,45,46,5,12,
        0,0,46,5,1,0,0,0,3,23,40,42
    ]

class ltlParser ( Parser ):

    grammarFileName = "ltl.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'|'", "'&'", "'U'", "'->'", "'<->'", 
                     "'X'", "'F'", "'G'", "'!'", "'('", "')'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "ID" ]

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


    class FContext(FormulaContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a ltlParser.FormulaContext
            super().__init__(parser)
            self.copyFrom(ctx)

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
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 23
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [6]:
                localctx = ltlParser.XContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 10
                self.match(ltlParser.T__5)
                self.state = 11
                self.formula(6)
                pass
            elif token in [7]:
                localctx = ltlParser.FContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 12
                self.match(ltlParser.T__6)
                self.state = 13
                self.formula(5)
                pass
            elif token in [8]:
                localctx = ltlParser.GContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 14
                self.match(ltlParser.T__7)
                self.state = 15
                self.formula(4)
                pass
            elif token in [9]:
                localctx = ltlParser.NotContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 16
                self.match(ltlParser.T__8)
                self.state = 17
                self.formula(3)
                pass
            elif token in [10]:
                localctx = ltlParser.ParenthesesContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 18
                self.match(ltlParser.T__9)
                self.state = 19
                self.formula(0)
                self.state = 20
                self.match(ltlParser.T__10)
                pass
            elif token in [12]:
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
                        self.match(ltlParser.T__2)
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
                        self.match(ltlParser.T__3)
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
                        self.match(ltlParser.T__4)
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
         




