from typing import NamedTuple, Self
from hashlib import sha1


def short_id(long_id):
    bytes_id = str(long_id).encode('utf-8')
    return sha1(bytes_id).hexdigest()[:2]

class Symbol:
    """Base class for terms and predicates"""


class Term(Symbol):
    """Base class for atoms, functions & variables"""


class Atom(Term):
    """A constant term, e.g., `c`"""

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Function(Term):
    """A function term, e.g., `f(c)`"""

    def __init__(self, name, args: list[Term]):
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self):
        args = ', '.join([repr(arg) for arg in self.args])
        return f'{self.name}({args})'


class Variable(Term):
    """A variable, e.g., `X` which takes on values of other terms"""

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f'{self.name}_{short_id(id(self))}'
    
    def __hash__(self):
        return id(self)
    
    def __eq__(self, other):
        return self is other


class Predicate(Symbol):
    """A predicate, e.g., `P(X, f(Y))`. Predicates can be assigned truth values."""

    def __init__(self, name, args: list[Term]):
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self):
        args = ', '.join([repr(arg) for arg in self.args])
        return f'{self.name}({args})'
    

class Cut(Predicate):
    """A special Prolog predicate (`!`) which controls backtracking behaviour."""
    def __init__(self):
        super().__init__(name="!", args=[])

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '!'


class Rule:
    """A Prolog rule, e.g,
    
    connected(A, C) :- connected(A, B), connected(B, C).
    """

    def __init__(self, head: Predicate, body: list[Predicate] = []):
        self.head = head
        self.body = body

    def __repr__(self):
        head = repr(self.head)
        if not self.body:
            return f'{head}.'
        body = ', '.join([repr(p) for p in self.body])
        return f'{head} :- {body}.'


def format_proof(query: Predicate, rules: list[Predicate], assignments: list, with_dontcare = False) -> str:
    output = [f'?- {query}.']
    for assignment in assignments:
        line = []
        for k, v in assignment.items():
            if not with_dontcare and k.name == '_':
                continue    
            line.append(f'{k} = {v}')
        if line:
            output.append('  ' + ', '.join(line))
    return '\n'.join(output)


def substitute(node: Symbol, substitution: dict[Variable, Term]) -> Symbol:
    """Replace all variables in a symbol (predicate or term) with its corresponding value.

    The value can be another variable.
    """
    match node:
        case Atom() as atom:
            return atom
        case Cut() as cut:
            return cut
        case Predicate(name=name, args=args):
            args = [substitute(arg, substitution) for arg in args]
            return Predicate(name=name, args=args)
        case Function(name=name, args=args):
            args = [substitute(arg, substitution) for arg in args]
            return Function(name=name, args=args)
        case Variable() as v:
            while v in substitution:
                v = substitution[v]
            return v


def relabel(rule: Rule):
    class Substitution(dict):
        def __missing__(self, v: Variable):
            self[v] = Variable(v.name)
            return self[v]

    substitution = Substitution()
    return Rule(
        head=substitute(rule.head, substitution),
        body=[substitute(p, substitution) for p in rule.body]
    )


def relabel(rule: Rule):
    variables = {}
    def _relabel(node: Symbol):
        match node:
            case Cut() as cut:
                return cut
            case Predicate(name=name, args=args):
                args = [_relabel(arg) for arg in args]
                return Predicate(name=name, args=args)
            case Variable(name=name) as v:
                if v not in variables:
                    variables[v] = Variable(name=name)
                return variables[v]
            case Function(name=name, args=args):
                args = [_relabel(arg) for arg in args]
                return Function(name=name, args=args)
            case _:
                return node

    return Rule(
        head=_relabel(rule.head),
        body=[_relabel(p) for p in rule.body]
    )


def instantiate(pred: Predicate, assignments):
    for assignment in assignments:
        pred = substitute(pred, assignment)
    return pred


def contains(term: Term, x: Variable):
    match term:
        case Variable() as y:
            return x == y
        case Function(args=args):
            return any(contains(arg, x) for arg in args)
        case _:
            return False


def collect_variables(term: Term):
    match term:
        case Variable() as v:
            return set([v])
        case Function(args=args):
            out = set()
            for arg in args:
                out |= collect_variables(arg)
            return out
        case _:
            return set()


def get_value(v, substitution):
    while v in substitution:
        v = substitution[v]
    return v


def unify(x: Symbol | list[Term], y: Symbol | list[Term]):
    match (x, y):
        case (Atom(), Atom()) if x.name == y.name:
            return {}
        case (Function(), Function()) if x.name == y.name and x.arity == y.arity:
            return unify(x.args, y.args)
        case (Predicate(), Predicate()) if x.name == y.name and x.arity == y.arity:
            return unify(x.args, y.args)
        case (Variable(), Variable()):
            if x == y:
                return {}
            else:
                return {x: y}
        case (Variable(), (Atom() | Function()) as term):
            if not contains(term, x):
                return {x: term}
        case ((Atom() | Function()) as term, Variable()):
            if not contains(term, y):
                return {y: term}
        case (list(), list()) if len(x) == len(y):
            current = {}
            for a, b in zip(x, y):
                a = substitute(a, current)
                b = substitute(b, current)

                if (new := unify(a, b)) is None:
                    return
                current |= new
            return current


def get_cuts(stack):
    return set(pred for pred in stack if isinstance(pred, Cut))


def cut_active(stack, cuts):
    return any(cut in cuts for cut in get_cuts(stack))


class QueryState(NamedTuple):
    rules: list[Rule]
    stack: list[Predicate]
    stack_depth: int = 0
    cuts: set[Cut] = set()
    partial_assignment: list[dict[Variable, Term]] = [{}]

    def make_new(self, **kwargs) -> Self:
        kwargs = self._asdict() | {'stack_depth': self.stack_depth + 1} | kwargs
        return QueryState(**kwargs)


def query(state: QueryState, search_tree):
    curr = {
        'current': state.stack,
        'current_depth': state.stack_depth,
        'children': []
    }
    search_tree.append(curr)

    if not state.stack:
        yield state.partial_assignment
        return

    print(state.stack_depth, "Current stack:", state.stack)
    predicate, stack = state.stack[0], state.stack[1:]

    if isinstance(predicate, Cut):
        state.cuts.add(predicate)
        yield from query(state.make_new(stack=stack), curr['children'])
        return

    for rule in state.rules:
        print(state.stack_depth, 'cut active:', cut_active(stack, state.cuts))
        if cut_active(stack, state.cuts):
            break

        rule = relabel(rule)
        print(state.stack_depth, "Trying to match", predicate, stack)
        if (assignment := unify(predicate, rule.head)) is not None:
            print(state.stack_depth, "Unified:", predicate, rule.head, state.partial_assignment + [assignment])
            new_stack = [substitute(p, assignment) for p in stack]

            if not rule.body:
                yield from query(state.make_new(stack=new_stack, partial_assignment=state.partial_assignment + [assignment]),
                                 curr['children'])
            else:
                body = [substitute(p, assignment) for p in rule.body]
                new_cuts = get_cuts(body)
                yield from query(state.make_new(stack=body + new_stack, partial_assignment=state.partial_assignment + [assignment]),
                                 curr['children'])
                for cut in new_cuts:
                    state.cuts.discard(cut)
        else:
            pass
            print(state.stack_depth, "NOunify:", predicate, rule.head, state.partial_assignment)
