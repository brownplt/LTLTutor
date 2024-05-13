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
    def __to_english__(self, depth=0):
        pass

    @staticmethod
    def equiv(formula1, formula2):
        areEquivalent(formula1, formula2)

    def get_indent(self, depth):
        return '  ' * depth

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
    
    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.operator} of {self.operand.__to_english__(depth+1)}"


class BinaryOperatorNode(LTLNode):
    def __init__(self, operator, left, right):
        super().__init__('BinaryOperator')
        self.operator = operator
        self.left = left
        self.right = right

    def __str__(self):
        return f'({str(self.left)} {self.operator} {str(self.right)})'
    
    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.operator} of {self.left.__to_english__(depth+1)}, {self.right.__to_english__(depth+1)} "


class LiteralNode(LTLNode):
    def __init__(self, value):
        super().__init__('Literal')
        self.value = value

    def __str__(self):
        return self.value
    
    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.value} holds"


class UntilNode(BinaryOperatorNode):
    symbol = UNTIL_SYMBOL
    def __init__(self, left, right):
        super().__init__(UntilNode.symbol, left, right)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.left.__to_english__(depth+1)} until {self.right.__to_english__(depth+1)}"


class NextNode(UnaryOperatorNode):
    symbol = NEXT_SYMBOL
    def __init__(self, operand):
        super().__init__(NextNode.symbol, operand)


    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}next, {self.operand.__to_english__(depth+1)}"


class GloballyNode(UnaryOperatorNode):
    symbol = GLOBALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(GloballyNode.symbol, operand)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}always, {self.operand.__to_english__(depth+1)}"


class FinallyNode(UnaryOperatorNode):
    symbol = FINALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(FinallyNode.symbol, operand)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}eventually, {self.operand.__to_english__(depth+1)}"


class OrNode(BinaryOperatorNode):

    symbol = OR_SYMBOL

    def __init__(self, left, right):
        super().__init__(OrNode.symbol, left, right)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.left.__to_english__(depth+1)} or {self.right.__to_english__(depth)}"


class AndNode(BinaryOperatorNode):
    symbol = AND_SYMBOL
    def __init__(self, left, right):
        super().__init__(AndNode.symbol, left, right)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.left.__to_english__(depth+1)} and {self.right.__to_english__(depth+1)}"


class NotNode(UnaryOperatorNode):
    symbol = NOT_SYMBOL
    def __init__(self, operand):
        super().__init__(NotNode.symbol, operand)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}not {self.operand.__to_english__(depth+1)}."

class ImpliesNode(BinaryOperatorNode):
    symbol = IMPLIES_SYMBOL
    def __init__(self, left, right):
        super().__init__(ImpliesNode.symbol, left, right)

    def __to_english__(self,depth=0):
        return f"\n{self.get_indent(depth)}if {self.left.__to_english__(depth+1)} then {self.right.__to_english__(depth+1)}."


class EquivalenceNode(BinaryOperatorNode):
    symbol = EQUIVALENCE_SYMBOL
    def __init__(self, left, right):
        super().__init__(EquivalenceNode.symbol, left, right)

    def __to_english__(self, depth=0):
        return f"\n{self.get_indent(depth)}{self.left.__to_english__()} if and only if {self.right.__to_english__(depth+1)}"



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

