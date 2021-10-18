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
    ('\{.+?\}',         'KV PAIR'),
]

lx = Lexer(rules, skip_whitespace=True)
# lx.input('erw = _abc + 12*(R4-623902)  ')
lx.input('We initially perform the {sequence alignment|stage} by generating {GluN1,GluN2,GluN3| sequence alignment } {MAAFT Server| Software }{7|version}  is used for the alignment using  {default|settings}.')

try:
    for tok in lx.tokens():
        print(tok)
except LexerError as err:
    print('LexerError at position %s' % err.pos)