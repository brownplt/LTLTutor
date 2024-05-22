 function ltlSyntaxDefs (hljs) {
    
    return {
        name: 'LTL',
        case_insensitive: false,
        keywords: ['G', 'F', 'X', 'U', 'always', 'eventually', 'until', 'next', '&', 'and', '|', 'or', '!', 'not', '->', 'implies',  '<->', 'iff'],
        aliases: ['ltl']
    };
}