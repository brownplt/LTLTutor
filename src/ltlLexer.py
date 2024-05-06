# Generated from ltl.g4 by ANTLR 4.13.1
from antlr4 import *
from io import StringIO
import sys
if sys.version_info[1] > 5:
    from typing import TextIO
else:
    from typing.io import TextIO


def serializedATN():
    return [
        4,0,12,55,6,-1,2,0,7,0,2,1,7,1,2,2,7,2,2,3,7,3,2,4,7,4,2,5,7,5,2,
        6,7,6,2,7,7,7,2,8,7,8,2,9,7,9,2,10,7,10,2,11,7,11,1,0,1,0,1,1,1,
        1,1,2,1,2,1,3,1,3,1,4,1,4,1,5,1,5,1,6,1,6,1,7,1,7,1,8,1,8,1,9,1,
        9,1,9,1,10,1,10,1,10,1,10,1,11,4,11,52,8,11,11,11,12,11,53,0,0,12,
        1,1,3,2,5,3,7,4,9,5,11,6,13,7,15,8,17,9,19,10,21,11,23,12,1,0,1,
        6,0,48,57,65,69,72,84,86,87,89,90,97,122,55,0,1,1,0,0,0,0,3,1,0,
        0,0,0,5,1,0,0,0,0,7,1,0,0,0,0,9,1,0,0,0,0,11,1,0,0,0,0,13,1,0,0,
        0,0,15,1,0,0,0,0,17,1,0,0,0,0,19,1,0,0,0,0,21,1,0,0,0,0,23,1,0,0,
        0,1,25,1,0,0,0,3,27,1,0,0,0,5,29,1,0,0,0,7,31,1,0,0,0,9,33,1,0,0,
        0,11,35,1,0,0,0,13,37,1,0,0,0,15,39,1,0,0,0,17,41,1,0,0,0,19,43,
        1,0,0,0,21,46,1,0,0,0,23,51,1,0,0,0,25,26,5,40,0,0,26,2,1,0,0,0,
        27,28,5,41,0,0,28,4,1,0,0,0,29,30,5,88,0,0,30,6,1,0,0,0,31,32,5,
        70,0,0,32,8,1,0,0,0,33,34,5,71,0,0,34,10,1,0,0,0,35,36,5,33,0,0,
        36,12,1,0,0,0,37,38,5,124,0,0,38,14,1,0,0,0,39,40,5,38,0,0,40,16,
        1,0,0,0,41,42,5,85,0,0,42,18,1,0,0,0,43,44,5,45,0,0,44,45,5,62,0,
        0,45,20,1,0,0,0,46,47,5,60,0,0,47,48,5,45,0,0,48,49,5,62,0,0,49,
        22,1,0,0,0,50,52,7,0,0,0,51,50,1,0,0,0,52,53,1,0,0,0,53,51,1,0,0,
        0,53,54,1,0,0,0,54,24,1,0,0,0,2,0,53,0
    ]

class ltlLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    X = 3
    F = 4
    G = 5
    NOT = 6
    OR = 7
    AND = 8
    U = 9
    IMPLIES = 10
    EQUIV = 11
    ID = 12

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'('", "')'", "'X'", "'F'", "'G'", "'!'", "'|'", "'&'", "'U'", 
            "'->'", "'<->'" ]

    symbolicNames = [ "<INVALID>",
            "X", "F", "G", "NOT", "OR", "AND", "U", "IMPLIES", "EQUIV", 
            "ID" ]

    ruleNames = [ "T__0", "T__1", "X", "F", "G", "NOT", "OR", "AND", "U", 
                  "IMPLIES", "EQUIV", "ID" ]

    grammarFileName = "ltl.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.13.1")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


