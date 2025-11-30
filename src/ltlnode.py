# Description: This file contains the classes for the nodes of the LTL syntax tree.

import os
import random

### TODO: Ideally, this should not be in 
### src, but mocked in the test directory.


from spotutils import areEquivalent


from ltlListener import ltlListener
from antlr4 import CommonTokenStream, ParseTreeWalker
from antlr4 import ParseTreeWalker, CommonTokenStream, InputStream
from ltlLexer import ltlLexer
from ltlParser import ltlParser
from abc import ABC, abstractmethod
import ltltoeng


SUPPORTED_SYNTAXES = ['Classic', 'Forge', 'Electrum']

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
        return areEquivalent(formula1, formula2)

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

    def exitU(self, ctx):
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
        return f"({self.operator} {self.operand.__forge__()})"
    
    def __electrum__(self):
        return f"({self.operator} {self.operand.__electrum__()})"


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
        return f"({self.left.__forge__()} {self.operator} {self.right.__forge__()})"
    
    def __electrum__(self):
        return f"({self.left.__electrum__()} {self.operator} {self.right.__electrum__()})"


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

        # For literals, use simpler phrasing
        # Note: We don't capitalize here because the literal is in quotes
        # and should remain as-is per capitalize_sentence() logic
        return f"'{self.value}'"
    
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
        lhs = self.left.__to_english__().rstrip('.')
        rhs = self.right.__to_english__().rstrip('.')
        return f"{lhs} until {rhs}"
    
    def __forge__(self):
        return f"({self.left.__forge__()} UNTIL {self.right.__forge__()})"
    
    def __electrum__(self):
        return f"({self.left.__forge__()} UNTIL {self.right.__forge__()})"


class NextNode(UnaryOperatorNode):
    symbol = NEXT_SYMBOL
    def __init__(self, operand):
        super().__init__(NextNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        op = self.operand.__to_english__().rstrip('.')
        return f"in the next step, {op}"
    
    def __forge__(self):
        return f"(NEXT_STATE {self.operand.__forge__()})"
    
    def __electrum__(self):
        return f"(AFTER {self.operand.__electrum__()})"


class GloballyNode(UnaryOperatorNode):
    symbol = GLOBALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(GloballyNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x

        op = self.operand.__to_english__().rstrip('.')
        patterns = [
            f"it is always the case that {op}",
            f"at all times, {op}",
            f"{op} is always true"
        ]

        english = ltltoeng.choose_best_sentence(patterns)
        return english
    
    def __forge__(self):
        return f"(ALWAYS {self.operand.__forge__()})"
    
    def __electrum__(self):
        return f"(ALWAYS {self.operand.__electrum__()})"


class FinallyNode(UnaryOperatorNode):
    symbol = FINALLY_SYMBOL
    def __init__(self, operand):
        super().__init__(FinallyNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        op = self.operand.__to_english__().rstrip('.')

        english = f"eventually, {op}"
        return english
    
    def __forge__(self):
        return f"(EVENTUALLY {self.operand.__forge__()})"
    
    def __electrum__(self):
        return f"(EVENTUALLY {self.operand.__electrum__()})"


class OrNode(BinaryOperatorNode):

    symbol = OR_SYMBOL

    def __init__(self, left, right):
        super().__init__(OrNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__().rstrip('.')
        rhs = self.right.__to_english__().rstrip('.')
        return f"either {lhs} or {rhs}"
    



class AndNode(BinaryOperatorNode):
    symbol = AND_SYMBOL
    def __init__(self, left, right):
        super().__init__(AndNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__().rstrip('.')
        rhs = self.right.__to_english__().rstrip('.')
        return f"both {lhs} and {rhs}"


class NotNode(UnaryOperatorNode):
    symbol = NOT_SYMBOL
    def __init__(self, operand):
        super().__init__(NotNode.symbol, operand)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x

        op = self.operand.__to_english__().rstrip('.')

        ## If the operand is a literal, we can just negate it
        if isinstance(self.operand, LiteralNode):
            return f"not {op}"
        else:
            return f"it is not the case that {op}"

class ImpliesNode(BinaryOperatorNode):
    symbol = IMPLIES_SYMBOL
    def __init__(self, left, right):
        super().__init__(ImpliesNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
            
        lhs = self.left.__to_english__().rstrip('.')
        rhs = self.right.__to_english__().rstrip('.')

        lhs = ltltoeng.normalize_embedded_clause(lhs)
        rhs = ltltoeng.normalize_embedded_clause(rhs)

        # Potential patterns:
        patterns = [
            f"if {lhs}, then {rhs}",
            f"{lhs} implies {rhs}",
            f"whenever {lhs}, then {rhs}"
        ]

        # Choose the most fluent pattern rather than picking randomly
        english = ltltoeng.choose_best_sentence(patterns)
        return english


class EquivalenceNode(BinaryOperatorNode):
    symbol = EQUIVALENCE_SYMBOL
    def __init__(self, left, right):
        super().__init__(EquivalenceNode.symbol, left, right)

    def __to_english__(self):
        x = ltltoeng.apply_special_pattern_if_possible(self)
        if x is not None:
            return x
        lhs = self.left.__to_english__().rstrip('.')
        rhs = self.right.__to_english__().rstrip('.')

        lhs = ltltoeng.normalize_embedded_clause(lhs)
        rhs = ltltoeng.normalize_embedded_clause(rhs)

        # Potential patterns:
        patterns = [
            f"{lhs} if and only if {rhs}",
            f"{lhs} exactly when {rhs}",
            f"{lhs} is equivalent to {rhs}"
        ]

        # Choose the most fluent pattern rather than picking randomly
        english = ltltoeng.choose_best_sentence(patterns)
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



