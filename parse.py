import re
from prolog import Rule, Predicate, Variable, Atom, Function, Cut, Term
from typing import NamedTuple
from enum import Enum


VARIABLE = re.compile(r'[A-Z_][A-Za-z0-9_]*')
NAME = re.compile(r'(?:[a-z0-9][A-Za-z0-9_]*)|!')
SPECIAL = re.compile(r'[().,]|:-')
WS = re.compile(r'\s+')


class TokenType(Enum):
    variable = 1
    name = 2
    special = 3


class Token(NamedTuple):
    type: TokenType
    value: str


def remove_comments(source):
    return re.sub(r'#.+', '', source)


def remove_whitespace(source):
    return re.sub(WS, '', source)


def tokenize(source):
    source = remove_comments(source)
    source = remove_whitespace(source)
    tokens = []
    while source:
        if match := re.match(VARIABLE, source):
            _type = TokenType.variable
        elif match := re.match(NAME, source):
            _type = TokenType.name
        elif match := re.match(SPECIAL, source):
            _type = TokenType.special
        else:
            raise Exception(f"Unexpected token: {source}")
        tokens.append(Token(_type, match[0]))
        source = source[match.end():]
    return tokens


class Parser:
    def __init__(self, source: str):
        self.tokens = tokenize(source)
        self.current_scope = {}

    def pop(self) -> Token:
        return self.tokens.pop(0)

    def parse(self) -> list[Rule]:
        rules = []
        while self.tokens:
            self.current_scope = {}
            rules.append(self.parse_rule())
        return rules

    def parse_rule(self) -> Rule:
        head = self.parse_head()
        token = self.pop()
        match token:
            case Token(type=TokenType.special, value='.'):
                return Rule(head=head)
            case Token(type=TokenType.special, value=':-'):
                body = self.parse_body()
                token = self.pop()
                if token.value != '.':
                    raise Exception('missing dot')
                return Rule(head=head, body=body)
            case _:
                raise Exception('parse err')

    def parse_head(self) -> Predicate:
        return self.parse_predicate()
    
    def parse_body(self) -> list[Predicate]:
        body = [self.parse_predicate()]
        while self.tokens[0].value == ',':
            self.pop()
            body.append(self.parse_predicate())
        return body
    
    def parse_predicate(self) -> Predicate:
        token = self.pop()
        if token.type != TokenType.name:
            raise Exception(f'parse err {token}')

        name = token.value
        if name == '!':
            return Cut()

        token = self.pop()
        if token.value != '(':
            raise Exception('parse err')

        args = self.parse_args()
        token = self.pop()
        if token.value != ')':
            raise Exception('parse err')

        return Predicate(name=name, args=args)

    def parse_args(self) -> list[Term]:
        if self.tokens[0].value == ')':
            return []

        args = [self.parse_term()]
        while self.tokens[0].value == ',':
            self.pop()
            args.append(self.parse_term())
        return args

    def parse_term(self) -> Term:
        token = self.pop()
        match token:
            case Token(type=TokenType.variable, value=name):
                if name == '_':
                    return Variable('_')
                if name not in self.current_scope:
                    self.current_scope[name] = Variable(name=name)
                return self.current_scope[name]
            case Token(type=TokenType.name, value=name):
                if self.tokens[0].value == '(':
                    self.pop()
                    fn = Function(name=name, args=self.parse_args())
                    token = self.pop()
                    if token.value != ')':
                        raise Exception('unclosed argument list')
                    return fn
                else:
                    return Atom(name=name)
            case _:
                raise Exception(f'parse err {token}')