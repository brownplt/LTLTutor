import * as ltlnode from '../src/ltlnode';
import * as codebook from '../src/codebook';


function testMisconception(code: codebook.MisconceptionCode, input: string, expected: string) {
    const ast = ltlnode.parseLTLString(input);
    const result = codebook.applyMisconception(ast, code).node.toString();
    expect(result).toBe(expected);
}


describe('Codebook mutator', () => {

    test (' applies no misconceptions to a literal', () => {
        const ast = ltlnode.parseLTLString('literal');
        const allApplicable = codebook.getAllApplicableMisconceptions(ast);

        expect(allApplicable.length).toBe(0);
    });


    test(' can apply precedence', () => {

        const input = 'a && (b || c)';
        const expected = '((a && b) || c)';
        testMisconception(codebook.MisconceptionCode.Precedence, input, expected)

        const input2 = '(a U d) && (b || (c <=> d))';
        const expected2 = "(((a U d) && b) || (c <=> d))";
        testMisconception(codebook.MisconceptionCode.Precedence, input2, expected2)
    });

});