import re
from prolog import Rule, Predicate, Variable, Atom, Function, List, Cut
from dataclasses import dataclass


VARIABLE = re.compile(r'[A-Z_][A-Za-z0-9_]*')
NAME = re.compile(r'(?:[a-z0-9][A-Za-z0-9_]*)|!')
SPECIAL = re.compile(r'[\[\]|().,]|:-')
WS = re.compile(r'\s+')


@dataclass
class Token:
    type: str
    value: str


def remove_comments(source):
    return re.sub(r'#.+', '', source)


def tokenize(source):
    source = re.sub(WS, '', source)
    tokens = []
    while source:
        if match := re.match(VARIABLE, source):
            tokens.append(Token('variable', match[0]))
            source = source[match.end():]
        elif match := re.match(NAME, source):
            tokens.append(Token('name', match[0]))
            source = source[match.end():]
        elif match := re.match(SPECIAL, source):
            tokens.append(Token('special', match[0]))
            source = source[match.end():]
        else:
            raise Exception(f"Unexpected token: {source}")
        
    return tokens


class Parser:
    def __init__(self, source):
        self.tokens = tokenize(remove_comments(source))
        self.scope = {}

    def parse(self):
        rules = []
        while self.tokens:
            self.scope = {}
            rules.append(self.parse_rule())
        return rules

    def parse_rule(self):
        head = self.parse_head()
        token = self.tokens.pop(0)
        match token:
            case Token(type='special', value='.'):
                return Rule(head=head)
            case Token(type='special', value=':-'):
                body = self.parse_body()
                token = self.tokens.pop(0)
                if token.value != '.':
                    raise Exception('missing dot')
                return Rule(head=head, body=body)
            case _:
                raise Exception('parse err')

    def parse_head(self):
        return self.parse_predicate()
    
    def parse_body(self):
        body = [self.parse_predicate()]
        while self.tokens[0].value == ',':
            self.tokens.pop(0)
            body.append(self.parse_predicate())
        return body
    
    def parse_predicate(self):
        token = self.tokens.pop(0)
        if token.type not in ('name',):
            raise Exception(f'parse err {token}')

        name = token.value
        if name == '!':
            return Cut()

        token = self.tokens.pop(0)
        if token.value != '(':
            raise Exception('parse err')

        args = self.parse_args()

        token = self.tokens.pop(0)
        if token.value != ')':
            raise Exception('parse err')

        return Predicate(name=name, args=args)

    def parse_args(self):
        if self.tokens[0].value == ')':
            self.tokens.pop(0)
            return []

        args = [self.parse_term()]
        while self.tokens[0].value == ',':
            self.tokens.pop(0)
            args.append(self.parse_term())
        return args

    def parse_term(self):
        token = self.tokens.pop(0)
        match token:
            case Token(type='variable', value=name):
                if name not in self.scope:
                    self.scope[name] = Variable(name=name)
                return self.scope[name]
            case Token(type='name', value=name):
                if self.tokens[0].value == '(':
                    if self.tokens[0].value == ']':
                        self.tokens.pop(0)
                        return Function(name=name, args=[])
                    self.tokens.pop(0)
                    fn = Function(name=name, args=self.parse_args())
                    token = self.tokens.pop(0)
                    if token.value != ')':
                        raise Exception('unclosed argument list')
                    return fn
                else:
                    return Atom(name=name)
            case Token(type='special', value='['):
                if self.tokens[0].value == ']':
                    self.tokens.pop(0)
                    return List()
                lst = self.parse_list()
                token = self.tokens.pop(0)
                if token.value != ']':
                    raise Exception(f'unclosed list {token}')
                return lst
            case _:
                raise Exception(f'parse err {token}')

        
    def parse_list(self):
        head = self.parse_term()
        if self.tokens[0].value == '|':
            self.tokens.pop(0)
            tail = self.parse_term()
            if not isinstance(tail, List) and not isinstance(tail, Variable):
                raise Exception(f'Expected a list or variable, got: {tail}')
            return List(args=[head, tail])
        
        arr = [head]
        while self.tokens[0].value == ',':
            self.tokens.pop(0)
            arr.append(self.parse_term())
        return List.from_list(arr)



