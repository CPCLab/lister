class LexerError(Exception):
    def __init__(self, pos):
        self.pos = pos