import unittest
import codebook
from ltlnode import parseLTLString

## TODO: Imports need an init.py

class TestCodebook(unittest.TestCase):
    def applyAndCheckMisconception(self, code, input, expected):
        ast = parseLTLString(input)
        result = str(codebook.applyMisconception(ast, code).node)
        self.assertEqual(result, expected)


    def test_applyMisconception(self):
        input = parseLTLString('a && (b || c)')
        expected = '((a && b) || c)'
        self.applyAndCheckMisconception(codebook.MisconceptionCode.Precedence, input, expected)


        input2 = parseLTLString('(a U d) && (b || (c <=> d))')
        expected2 = "(((a U d) && b) || (c <=> d))"
        self.applyAndCheckMisconception(codebook.MisconceptionCode.Precedence, input2, expected)

    def test_getAllApplicableMisconceptions(self):
        input = parseLTLString('literal')
        result = codebook.getAllApplicableMisconceptions(input)
        self.assertEqual(len(result), 0)

    # Add more test methods for other functions in codebook.py

if __name__ == '__main__':
    unittest.main()
