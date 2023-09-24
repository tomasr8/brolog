import re
from enum import Enum, auto
from typing import NamedTuple


VARIABLE = re.compile(r"[A-Z_][A-Za-z0-9_]*")
NAME = re.compile(r"(?:[a-z0-9][A-Za-z0-9_]*)|!")
SPECIAL = re.compile(r"[\[\]|().,]|:-")
COMMENT = re.compile(r"#.*")
NL = re.compile(r"\r?\n")
WS = re.compile(r"\s+")


class LexerError(Exception):
    def __init__(self, message: str, *, line: int, column: int) -> None:
        super().__init__(message)
        self.line = line
        self.column = column


class TokenType(Enum):
    variable = auto()
    name = auto()
    special = auto()


class Token(NamedTuple):
    type: TokenType
    value: str
    line: int
    column: int


def tokenize(source: str) -> list[Token]:
    line, column = 1, 1
    tokens = []
    while source:
        if match := re.match(NL, source):
            line += 1
            column = 1
        elif (match := re.match(WS, source)) or (match := re.match(COMMENT, source)):
            column += len(match[0])
        elif match := re.match(VARIABLE, source):
            _type = TokenType.variable
            tokens.append(Token(_type, match[0], line, column))
            column += len(match[0])
        elif match := re.match(NAME, source):
            _type = TokenType.name
            tokens.append(Token(_type, match[0], line, column))
            column += len(match[0])
        elif match := re.match(SPECIAL, source):
            _type = TokenType.special
            tokens.append(Token(_type, match[0], line, column))
            column += len(match[0])
        else:
            msg = f"Unexpected token: <{source[0]}>"
            raise LexerError(msg, line=line, column=column)
        source = source[match.end() :]
    return tokens
