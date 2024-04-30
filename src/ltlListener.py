# Generated from ltl.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
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


    # Enter a parse tree produced by ltlParser#F.
    def enterF(self, ctx:ltlParser.FContext):
        pass

    # Exit a parse tree produced by ltlParser#F.
    def exitF(self, ctx:ltlParser.FContext):
        pass


    # Enter a parse tree produced by ltlParser#implication.
    def enterImplication(self, ctx:ltlParser.ImplicationContext):
        pass

    # Exit a parse tree produced by ltlParser#implication.
    def exitImplication(self, ctx:ltlParser.ImplicationContext):
        pass


    # Enter a parse tree produced by ltlParser#G.
    def enterG(self, ctx:ltlParser.GContext):
        pass

    # Exit a parse tree produced by ltlParser#G.
    def exitG(self, ctx:ltlParser.GContext):
        pass


    # Enter a parse tree produced by ltlParser#X.
    def enterX(self, ctx:ltlParser.XContext):
        pass

    # Exit a parse tree produced by ltlParser#X.
    def exitX(self, ctx:ltlParser.XContext):
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