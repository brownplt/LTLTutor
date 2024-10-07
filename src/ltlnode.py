# Description: This file contains the classes for the nodes of the LTL syntax tree.

from ltlListener import ltlListener
from antlr4 import CommonTokenStream, ParseTreeWalker
from antlr4 import ParseTreeWalker, CommonTokenStream, InputStream
from ltlLexer import ltlLexer
from ltlParser import ltlParser
from abc import ABC, abstractmethod
from spotutils import areEquivalent
import random
import ltltoeng
import re



SUPPORTED_SYNTAXES = ['classic', 'forge', 'electrum']

## Should these come from the lexer instead of being placed here
IMPLIES_SYMBOL = '->'
EQUIVALENCE_SYMBOL = '<->'
AND_SYMBOL = '&'
OR_SYMBOL = '|'
NOT_SYMBOL = '!'
NEXT_SYMBOL = 'X'
GLOBALLY_SYMBOL = 'G'
FINALLY_SYMBOL = 'F'
UNTIL_SYMBOL = 'U'

  
## TODO: Too much is based on the Exact syntax. We should be able to
## switch syntaxes. Should this be server side or client side?
## If server side, we should have a way to switch syntaxes (__str__ vs __str__(syntax))



class LTLNode(ABC):
    def __init__(self, type):
        self.type = type

    """
        LTL Node in Classic/ Spot Syntax
    """
    @abstractmethod
    def __str__(self):
        pass

    """
        LTL Node in English
    """
    @abstractmethod
    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        # We should draw inspiration from:
        # https://matthewbdwyer.github.io/psp/patterns/ltl.html
        pass

    """
        LTLNode in Forge Syntax
    """
    @abstractmethod
    def __forge__(self):
        pass
    
    """
        LTLNode in Electrum Syntax
    """
    @abstractmethod
    def __electrum__(self):
        pass


    @staticmethod
    def equiv(formula1, formula2):
        areEquivalent(formula1, formula2)



class ltlListenerImpl(ltlListener) :
    def __init__(self):
        self.stack = []

    def exitDisjunction(self, ctx):
        right = self.stack.pop()
        left = self.stack.pop()
        orNode = OrNode(left, right)
        self.stack.append(orNode)

    def exitConjunction(self, ctx):
        right = self.stack.pop()
        left = self.stack.pop()
        andNode = AndNode(left, right)
        self.stack.append(andNode)

    def exitUntil(self, ctx):
        right = self.stack.pop()
        left = self.stack.pop()
        untilNode = UntilNode(left, right)
        self.stack.append(untilNode)

    def exitImplication(self, ctx):
        right = self.stack.pop()
        left = self.stack.pop()
        impliesNode = ImpliesNode(left, right)
        self.stack.append(impliesNode)

    def exitEquivalence(self, ctx):
        right = self.stack.pop()
        left = self.stack.pop()
        equivNode = EquivalenceNode(left, right)
        self.stack.append(equivNode)

    def exitX(self, ctx):
        operand = self.stack.pop()
        nextNode = NextNode(operand)
        self.stack.append(nextNode)

    def exitF(self, ctx):
        operand = self.stack.pop()
        finallyNode = FinallyNode(operand)
        self.stack.append(finallyNode)

    def exitG(self, ctx):
        operand = self.stack.pop()
        globallyNode = GloballyNode(operand)
        self.stack.append(globallyNode)

    def exitNot(self, ctx):
        operand = self.stack.pop()
        notNode = NotNode(operand)
        self.stack.append(notNode)

    def exitParentheses(self, ctx):
        formula = self.stack.pop()
        self.stack.append(formula)

    def exitAtomicFormula(self, ctx):
        value = ctx.ID().getText()
        literalNode = LiteralNode(value)
        self.stack.append(literalNode)

    def getRootFormula(self):
        return self.stack[-1]


class UnaryOperatorNode(LTLNode):
    def __init__(self, operator, operand):
        super().__init__('UnaryOperator')
        self.operator = operator
        self.operand = operand

    def __str__(self):
        return f'({self.operator} {str(self.operand)})'
    
    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        return self.__str__()
    
    def __forge__(self):
        return f"{self.operator} {self.operand.__forge__()}"
    
    def __electrum__(self):
        return f"{self.operator} {self.operand.__electrum__()}"


class BinaryOperatorNode(LTLNode):
    def __init__(self, operator, left, right):
        super().__init__('BinaryOperator')
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return f'({str(self.left)} {self.operator} {str(self.right)})'
    
    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        return self.__str__()
    
    def __forge__(self):
        return f"{self.left.__forge__()} {self.operator} {self.right.__forge__()}"
    
    def __electrum__(self):
        return f"{self.left.__electrum__()} {self.operator} {self.right.__electrum__()}"


class LiteralNode(LTLNode):
    def __init__(self, value):
        super().__init__('Literal')
        self.value = value

    def __str__(self):
        return self.value
    
    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x

        ### TODO: COuld we override so that this is more meaningful
        # for some cases?
        return f"'{self.value}' holds"
    
    def __forge__(self):
        return self.value
    
    def __electrum__(self):
        return self.value


class UntilNode(BinaryOperatorNode):
    symbol = UNTIL_SYMBOL
    def __init__(self, left, right):
        super().__init__(UntilNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__()
        rhs = self.right.__to_english__()
        english = f"{lhs} until {rhs}."
        return english
    
    def __forge__(self):
        return f"{self.left.__forge__()} UNTIL {self.right.__forge__()}"
    
    def __electrum__(self):
        return f"{self.left.__electrum__()} UNTIL {self.right.__electrum__()}"


class NextNode(UnaryOperatorNode):
    symbol = NEXT_SYMBOL
    def __init__(self, operand):
        super().__init__(NextNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        op = self.operand.__to_english__()
        english = f"in the next state, {op}."
        return english
    
    def __forge__(self):
        return f"NEXT_STATE {self.operand.__forge__()}"
    
    def __electrum__(self):
        return f"NEXT {self.operand.__electrum__()}"


class GloballyNode(UnaryOperatorNode):
    symbol = GLOBALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(GloballyNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x


        op = self.operand.__to_english__()
        patterns = [
            f"it is always the case that {op}",
            f"in all future states, {op}",
            f"globally, {op}"
        ]

        english = random.choice(patterns)
        return english
    
    def __forge__(self):
        return f"ALWAYS {self.operand.__forge__()}"
    
    def __electrum__(self):
        return f"ALWAYS {self.operand.__electrum__()}"


class FinallyNode(UnaryOperatorNode):
    symbol = FINALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(FinallyNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        op = self.operand.__to_english__()

        patterns = [
            f"eventually, {op}",
            f"now or in the future, {op}",
            f"at this or some future point, {op}"
        ]


        english = f"eventually, {op}"
        return english
    
    def __forge__(self):
        return f"EVENTUALLY {self.operand.__forge__()}"
    
    def __electrum__(self):
        return f"EVENTUALLY {self.operand.__electrum__()}"


class OrNode(BinaryOperatorNode):

    symbol = OR_SYMBOL

    def __init__(self, left, right):
        super().__init__(OrNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__()
        rhs = self.right.__to_english__()
        english = f"{lhs} or {rhs}."
        return english
    



class AndNode(BinaryOperatorNode):
    symbol = AND_SYMBOL
    def __init__(self, left, right):
        super().__init__(AndNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__()
        rhs = self.right.__to_english__()
        english = f"{lhs} and {rhs}."
        return english


class NotNode(UnaryOperatorNode):
    symbol = NOT_SYMBOL
    def __init__(self, operand):
        super().__init__(NotNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x

        op = self.operand.__to_english__()

        ## If the operand is a literal, we can just negate it
        if isinstance(self.operand, LiteralNode):
            english = f"{op}"
            # Replace 'holds' with does not hold in english.
            if "holds" in english:
                english = english.replace("holds", "does not hold")
        ## TODO: We can start donig some more. better special cases.
        else:
            english = f"it is not the case that {op}."
        return english

class ImpliesNode(BinaryOperatorNode):
    symbol = IMPLIES_SYMBOL
    def __init__(self, left, right):
        super().__init__(ImpliesNode.symbol, left, right)

    def __to_english__(self,depth=0):
        lhs = self.left.__to_english__()
        rhs = self.right.__to_english__()

        # Potential patterns:
        patterns = [
            f"if {lhs}, then {rhs}",
            f"{rhs} is necessary for {lhs}"
        ]

        # Choose a pattern randomly, and then return the corrected sentence
        english = random.choice(patterns)
        return english


class EquivalenceNode(BinaryOperatorNode):
    symbol = EQUIVALENCE_SYMBOL
    def __init__(self, left, right):
        super().__init__(EquivalenceNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__()
        rhs = self.right.__to_english__()

        # Potential patterns:
        patterns = [
            f"{lhs} is necessary and sufficient for {rhs}",
            f"{lhs} exactly when {rhs}",
            f"{lhs} is equivalent to {rhs}",
            f"{lhs} if and only if {rhs}"
        ]

        # Choose a pattern randomly, and then return the corrected sentence
        english = random.choice(patterns)
        return english



def parse_ltl_string(s):
    # Create an input stream from the string
    input_stream = InputStream(s)

    # Create a lexer and a token stream
    lexer = ltlLexer(input_stream)
    token_stream = CommonTokenStream(lexer)

    # Create the parser and parse the input
    parser = ltlParser(token_stream)
    tree = parser.ltl()

    # Create a listener
    listener = ltlListenerImpl()

    # Create a ParseTreeWalker and walk the parse tree with the listener
    walker = ParseTreeWalker()
    walker.walk(listener, tree)

    # Get the root of the syntax tree
    root = listener.getRootFormula()

    return root



