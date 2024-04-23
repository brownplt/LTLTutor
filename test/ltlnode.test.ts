import * as ltlnode from '../src/ltlnode';

describe('parseLTLString', () => { 
    test.each([
        ['a', ltlnode.LiteralNode],
        ['(abc)', ltlnode.LiteralNode],
        ['a && b', ltlnode.AndNode],
        ['a || b', ltlnode.OrNode],
        ['!a', ltlnode.NotNode],
        ['a => b', ltlnode.ImpliesNode],
        ['a <=> b', ltlnode.EquivalenceNode],
        ['X(a)', ltlnode.NextNode],
        ['F(a)', ltlnode.FinallyNode],
        ['G(a)', ltlnode.GloballyNode],
        ['X a && b', ltlnode.NextNode],
        ['(X a) && b', ltlnode.AndNode],
        ['a U b', ltlnode.UntilNode]
    ])('Can parse well formed strings', (input, expected) => {
        expect(ltlnode.parseLTLString(input)).toBeInstanceOf(expected);
    });
});

