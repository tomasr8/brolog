import re
from hashlib import sha1
from typing import Self


def short_id(long_id: int) -> str:
    bytes_id = str(long_id).encode("utf-8")
    return sha1(bytes_id, usedforsecurity=False).hexdigest()[:2]


class Symbol:
    """Base class for terms and predicates"""


class Term(Symbol):
    """Base class for atoms, functions & variables"""


class Atom(Term):
    """A constant term, e.g., `c`"""

    def __init__(self, name: str) -> None:
        self.name = name

    def __repr__(self) -> str:
        return self.name


class Function(Term):
    """A function term, e.g., `f(c)`"""

    def __init__(self, name: str, args: list[Term]) -> None:
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self) -> str:
        args = ", ".join([repr(arg) for arg in self.args])
        return f"{self.name}({args})"


class List(Function):
    """Prolog-style lists e.g. [1,2] or [H|T]"""

    def __init__(self, name: str = "<array>", args: list[Term] | None = None) -> None:
        match args:
            case None | []:
                super().__init__(name, args=[])
            case [head]:
                super().__init__(name, args=[head, List()])
            case [head, tail]:
                super().__init__(name, args=[head, tail])

    @property
    def head(self) -> Term | None:
        if self.args:
            return self.args[0]

    @property
    def tail(self) -> Term | None:
        if len(self.args) > 1:
            return self.args[1]

    def __repr__(self) -> str:
        match (self.head, self.tail):
            case None, None:
                return "[]"
            case head, None:
                return f"[{head}]"
            case head, Variable() as tail:
                return f"[{head}|{tail}]"
            case head, List(args=[]) as tail:
                return f"[{head}]"
            case head, List() as tail:
                # unwrap extra '[]'
                tail = re.sub(r"^\[(.+)\]$", r"\1", str(tail))
                return f"[{head},{tail}]"
            case head, tail:
                # List() is just a function so technically tail can be any type like an atom
                # e.g. [1|2] which is not a valid list but is syntactically correct
                return f"[{head}|{tail}]"

    @classmethod
    def from_list(cls: type[Self], arr: list[Term]) -> Self:
        if not arr:
            return cls()
        return cls(args=[arr[0], cls.from_list(arr[1:])])


class Variable(Term):
    """A variable, e.g., `X` which takes on values of other terms"""

    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"{self.name}_{short_id(id(self))}"

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: Self) -> bool:
        return self is other


class Predicate(Symbol):
    """A predicate, e.g., `P(X, f(Y))`. Predicates can be assigned truth values."""

    def __init__(self, name: str, args: list[Term]) -> None:
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self) -> str:
        args = ", ".join([repr(arg) for arg in self.args])
        return f"{self.name}({args})"


class Cut(Predicate):
    """A special Prolog predicate (`!`) which controls backtracking behaviour."""

    def __init__(self) -> None:
        super().__init__(name="!", args=[])

    def __hash__(self) -> int:
        return id(self)

    def __repr__(self) -> str:
        return "!"


class Rule:
    """A Prolog rule, e.g,

    connected(A, C) :- connected(A, B), connected(B, C).
    """

    def __init__(self, head: Predicate, body: list[Predicate] | None = None) -> None:
        self.head = head
        self.body = body or []

    def __repr__(self) -> str:
        head = repr(self.head)
        if not self.body:
            return f"{head}."
        body = ", ".join([repr(p) for p in self.body])
        return f"{head} :- {body}."
