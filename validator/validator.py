from Lexer import Lexer
from LexerError import LexerError

rules = [
    ('\d+',             'NUMBER'),
    ('[a-zA-Z_]\w*',    'IDENTIFIER'),
    ('\+',              'PLUS'),
    ('\-',              'MINUS'),
    ('\*',              'MULTIPLY'),
    ('\/',              'DIVIDE'),
    ('\(',              'LP'),
    ('\)',              'RP'),
    ('=',               'EQUALS'),
]

lx = Lexer(rules, skip_whitespace=True)
lx.input('erw = _abc + 12*(R4-623902)  ')

try:
    for tok in lx.tokens():
        print(tok)
except LexerError as err:
    print('LexerError at position %s' % err.pos)