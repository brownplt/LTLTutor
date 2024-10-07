# Generated from ltl.g4 by ANTLR 4.9.2
from antlr4 import *
if __name__ is not None and "." in __name__:
    from .ltlParser import ltlParser
else:
    from ltlParser import ltlParser

# This class defines a complete listener for a parse tree produced by ltlParser.
class ltlListener(ParseTreeListener):

    # Enter a parse tree produced by ltlParser#ltl.
    def enterLtl(self, ctx:ltlParser.LtlContext):
        pass

    # Exit a parse tree produced by ltlParser#ltl.
    def exitLtl(self, ctx:ltlParser.LtlContext):
        pass


    # Enter a parse tree produced by ltlParser#next.
    def enterNext(self, ctx:ltlParser.NextContext):
        pass

    # Exit a parse tree produced by ltlParser#next.
    def exitNext(self, ctx:ltlParser.NextContext):
        pass


    # Enter a parse tree produced by ltlParser#always.
    def enterAlways(self, ctx:ltlParser.AlwaysContext):
        pass

    # Exit a parse tree produced by ltlParser#always.
    def exitAlways(self, ctx:ltlParser.AlwaysContext):
        pass


    # Enter a parse tree produced by ltlParser#parentheses.
    def enterParentheses(self, ctx:ltlParser.ParenthesesContext):
        pass

    # Exit a parse tree produced by ltlParser#parentheses.
    def exitParentheses(self, ctx:ltlParser.ParenthesesContext):
        pass


    # Enter a parse tree produced by ltlParser#not.
    def enterNot(self, ctx:ltlParser.NotContext):
        pass

    # Exit a parse tree produced by ltlParser#not.
    def exitNot(self, ctx:ltlParser.NotContext):
        pass


    # Enter a parse tree produced by ltlParser#equivalence.
    def enterEquivalence(self, ctx:ltlParser.EquivalenceContext):
        pass

    # Exit a parse tree produced by ltlParser#equivalence.
    def exitEquivalence(self, ctx:ltlParser.EquivalenceContext):
        pass


    # Enter a parse tree produced by ltlParser#conjunction.
    def enterConjunction(self, ctx:ltlParser.ConjunctionContext):
        pass

    # Exit a parse tree produced by ltlParser#conjunction.
    def exitConjunction(self, ctx:ltlParser.ConjunctionContext):
        pass


    # Enter a parse tree produced by ltlParser#disjunction.
    def enterDisjunction(self, ctx:ltlParser.DisjunctionContext):
        pass

    # Exit a parse tree produced by ltlParser#disjunction.
    def exitDisjunction(self, ctx:ltlParser.DisjunctionContext):
        pass


    # Enter a parse tree produced by ltlParser#implication.
    def enterImplication(self, ctx:ltlParser.ImplicationContext):
        pass

    # Exit a parse tree produced by ltlParser#implication.
    def exitImplication(self, ctx:ltlParser.ImplicationContext):
        pass


    # Enter a parse tree produced by ltlParser#eventually.
    def enterEventually(self, ctx:ltlParser.EventuallyContext):
        pass

    # Exit a parse tree produced by ltlParser#eventually.
    def exitEventually(self, ctx:ltlParser.EventuallyContext):
        pass


    # Enter a parse tree produced by ltlParser#until.
    def enterUntil(self, ctx:ltlParser.UntilContext):
        pass

    # Exit a parse tree produced by ltlParser#until.
    def exitUntil(self, ctx:ltlParser.UntilContext):
        pass


    # Enter a parse tree produced by ltlParser#literal.
    def enterLiteral(self, ctx:ltlParser.LiteralContext):
        pass

    # Exit a parse tree produced by ltlParser#literal.
    def exitLiteral(self, ctx:ltlParser.LiteralContext):
        pass


    # Enter a parse tree produced by ltlParser#atomicFormula.
    def enterAtomicFormula(self, ctx:ltlParser.AtomicFormulaContext):
        pass

    # Exit a parse tree produced by ltlParser#atomicFormula.
    def exitAtomicFormula(self, ctx:ltlParser.AtomicFormulaContext):
        pass



del ltlParser