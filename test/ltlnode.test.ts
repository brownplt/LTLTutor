import * as ltlnode from '../src/ltlnode';

describe('parseLTLString', () => { 
    test('Can parse well formed strings', () => {
        
        expect(ltlnode.parseLTLString('a')).toBeInstanceOf(ltlnode.LiteralNode);
        expect(ltlnode.parseLTLString('(abc)')).toBeInstanceOf(ltlnode.LiteralNode);
        expect(ltlnode.parseLTLString('a && b')).toBeInstanceOf(ltlnode.AndNode);
        expect(ltlnode.parseLTLString('a || b')).toBeInstanceOf(ltlnode.OrNode);
        expect(ltlnode.parseLTLString('!a')).toBeInstanceOf(ltlnode.NotNode);
        expect(ltlnode.parseLTLString('a => b')).toBeInstanceOf(ltlnode.ImpliesNode);
        expect(ltlnode.parseLTLString('a <=> b')).toBeInstanceOf(ltlnode.EquivalenceNode);
        expect(ltlnode.parseLTLString('X(a)')).toBeInstanceOf(ltlnode.NextNode);
        expect(ltlnode.parseLTLString('F(a)')).toBeInstanceOf(ltlnode.FinallyNode);
        expect(ltlnode.parseLTLString('G(a)')).toBeInstanceOf(ltlnode.GloballyNode);


        expect(ltlnode.parseLTLString('X a && b')).toBeInstanceOf(ltlnode.NextNode);
        expect(ltlnode.parseLTLString('(X a) && b')).toBeInstanceOf(ltlnode.AndNode);
        expect(ltlnode.parseLTLString('a U b')).toBeInstanceOf(ltlnode.UntilNode);
    });
});

