# Description: This file contains the classes for the nodes of the LTL syntax tree.

from ltlListener import ltlListener
from antlr4 import CommonTokenStream, ParseTreeWalker
from antlr4 import ParseTreeWalker, CommonTokenStream, InputStream
from ltlLexer import ltlLexer
from ltlParser import ltlParser
from abc import ABC, abstractmethod
from spotutils import areEquivalent


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

class LTLNode(ABC):
    def __init__(self, type):
        self.type = type

    @abstractmethod
    def __str__(self):
        pass


    @abstractmethod
    def __to_english__(self):
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
        return f"{self.operator} of {self.operand.__to_english__()}"


class BinaryOperatorNode(LTLNode):
    def __init__(self, operator, left, right):
        super().__init__('BinaryOperator')
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return f'({str(self.left)} {self.operator} {str(self.right)})'
    
    def __to_english__(self):
        return f"{self.operator} of {self.left.__to_english__()}, {self.right.__to_english__()} "


class LiteralNode(LTLNode):
    def __init__(self, value):
        super().__init__('Literal')
        self.value = value

    def __str__(self):
        return self.value
    
    def __to_english__(self):
        return self.value


class UntilNode(BinaryOperatorNode):
    def __init__(self, left, right):
        super().__init__(UNTIL_SYMBOL, left, right)

    def __to_english__(self):
        return f"{self.left.__to_english__()} holds until {self.right.__to_english__()} holds."


class NextNode(UnaryOperatorNode):
    def __init__(self, operand):
        super().__init__(NEXT_SYMBOL, operand)

    def __to_english__(self):
        return f"{self.operand.__to_english__()} holds in the next state."


class GloballyNode(UnaryOperatorNode):
    def __init__(self, operand):
        super().__init__(GLOBALLY_SYMBOL, operand)

    def __to_english__(self):
        return f"It is always the case that {self.operand.__to_english__()} holds."


class FinallyNode(UnaryOperatorNode):
    def __init__(self, operand):
        super().__init__(FINALLY_SYMBOL, operand)

    def __to_english__(self):
        return f"It is eventually the case that {self.operand.__to_english__()} holds."


class OrNode(BinaryOperatorNode):
    def __init__(self, left, right):
        super().__init__(OR_SYMBOL, left, right)

    def __to_english__(self):
        return f"{self.left.__to_english__()} or {self.right.__to_english__()} hold."


class AndNode(BinaryOperatorNode):
    def __init__(self, left, right):
        super().__init__(AND_SYMBOL, left, right)

    def __to_english__(self):
        return f"{self.left.__to_english__()} and {self.right.__to_english__()} hold."


class NotNode(UnaryOperatorNode):
    def __init__(self, operand):
        super().__init__(NOT_SYMBOL, operand)

    def __to_english__(self):
        return f"{self.operand.__to_english__()} does not hold."

class ImpliesNode(BinaryOperatorNode):
    def __init__(self, left, right):
        super().__init__(IMPLIES_SYMBOL, left, right)

    def __to_english__(self):
        return f"If {self.left.__to_english__()} then {self.right.__to_english__()}."


class EquivalenceNode(BinaryOperatorNode):
    def __init__(self, left, right):
        super().__init__(EQUIVALENCE_SYMBOL, left, right)

    def __to_english__(self):
        return f"{self.left.__to_english__()} if and only if {self.right.__to_english__()}."



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

