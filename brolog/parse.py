from brolog.lex import Token, TokenType, tokenize
from brolog.objects import Atom, Cut, Function, List, Predicate, Rule, Term, Variable


class ParseError(Exception):
    def __init__(self, message: str, token: Token | None = None) -> None:
        super().__init__(message)
        self.token = token


class Parser:
    def __init__(self, source: str) -> None:
        self.tokens = tokenize(source)
        self.current_scope = {}

    def pop(self) -> Token:
        if not self.tokens:
            msg = "Unexpected end of file"
            raise ParseError(msg)

        return self.tokens.pop(0)

    def parse(self, *, head_only: bool = False) -> list[Rule]:
        if head_only:
            return self.parse_head()
        return self.parse_rules()

    def parse_rules(self) -> list[Rule]:
        rules = []
        while self.tokens:
            self.current_scope = {}
            rules.append(self.parse_rule())
        return rules

    def parse_rule(self) -> Rule:
        head = self.parse_head()
        token = self.pop()
        match token:
            case Token(type=TokenType.special, value="."):
                return Rule(head=head)
            case Token(type=TokenType.special, value=":-"):
                body = self.parse_body()
                token = self.pop()
                if token.value != ".":
                    msg = 'Expected "." at the end of a rule, but got "{token.value}"'
                    raise ParseError(msg, token)
                return Rule(head=head, body=body)
            case _:
                msg = f"Unexpected token while parsing rule: {token.value}"
                raise ParseError(msg, token)

    def parse_head(self) -> Predicate:
        return self.parse_predicate()

    def parse_body(self) -> list[Predicate]:
        body = [self.parse_predicate()]
        while self.tokens[0].value == ",":
            self.pop()
            body.append(self.parse_predicate())
        return body

    def parse_predicate(self) -> Predicate:
        token = self.pop()
        if token.type != TokenType.name:
            msg = f"Expected a name, but got {token.value}"
            raise ParseError(msg, token)

        name = token.value
        if name == "!":
            return Cut()

        token = self.pop()
        if token.value != "(":
            msg = f"Expected '(', but got {token.value}"
            raise ParseError(msg, token)

        args = self.parse_args()
        token = self.pop()
        if token.value != ")":
            msg = f"Expected ')', but got {token.value}"
            raise ParseError(msg, token)

        return Predicate(name=name, args=args)

    def parse_args(self) -> list[Term]:
        if not self.tokens:
            msg = "Unexpected end of file while parsing argument list"
            raise ParseError(msg)

        if self.tokens[0].value == ")":
            return []

        args = [self.parse_term()]
        while self.tokens and self.tokens[0].value == ",":
            self.pop()
            args.append(self.parse_term())
        return args

    def parse_term(self) -> Term:
        token = self.pop()
        match token:
            case Token(type=TokenType.variable, value=name):
                if name == "_":
                    return Variable("_")
                if name not in self.current_scope:
                    self.current_scope[name] = Variable(name=name)
                return self.current_scope[name]
            case Token(type=TokenType.name, value=name):
                if self.tokens[0].value == "(":
                    return self.parse_function(name)
                return Atom(name=name)
            case Token(type=TokenType.special, value="["):
                return self.parse_list()
            case _:
                msg = f"Unexpected token while parsing term: {token.value}"
                raise ParseError(msg, token)

    def parse_function(self, name: str) -> Function:
        self.pop()
        fn = Function(name=name, args=self.parse_args())
        token = self.pop()
        if token.value != ")":
            msg = f"Expected ')', but got {token.value}"
            raise ParseError(msg, token)
        return fn

    def parse_list(self) -> List:
        if self.tokens[0].value == "]":
            self.pop()
            return List()

        head = self.parse_term()
        if self.tokens[0].value == "|":
            old_token = self.pop()
            tail = self.parse_term()
            if not isinstance(tail, List) and not isinstance(tail, Variable):
                msg = f"Expected a list or variable, but got: {tail}"
                raise ParseError(msg, old_token)
            token = self.pop()
            if token.value != "]":
                msg = f"Expected ']', but got {token.value}"
                raise ParseError(msg, token)
            return List(args=[head, tail])

        arr = [head]
        while self.tokens[0].value == ",":
            self.pop()
            arr.append(self.parse_term())

        token = self.pop()
        if token.value != "]":
            msg = f"Expected ']', but got {token.value}"
            raise ParseError(msg, token)

        return List.from_list(arr)
