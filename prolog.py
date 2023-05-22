import itertools
from typing import Self
from pathlib import Path
import re


class Symbol:
    pass

class Term(Symbol):
    pass


class Atom(Term):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class Function(Term):
    def __init__(self, name, args: list[Term]):
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self):
        args = ', '.join([repr(arg) for arg in self.args])
        return f'{self.name}({args})'


class Variable(Term):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        short_id = str(id(self))[-2:]
        return f'{self.name}_{short_id}..'
    
    def __hash__(self):
        return id(self)
    
    def __eq__(self, other):
        return self is other


class List(Function):
    def __init__(self, name: str = '<array>', args: list[Term] = []):
        # print("ARGS", args)
        match args:
            case []:
                super().__init__(name, args=[])
            case [head]:
                super().__init__(name, args=[head, List()])
            case [head, tail]:
                super().__init__(name, args=[head, tail])

            # case head, (List() | Variable()) as tail:
            #     super().__init__(name, args=[head, tail])
            # case _:
            #     raise TypeError("Bad arguments")

    @property
    def head(self):
        if self.args:
            return self.args[0]

    @property
    def tail(self):
        if len(self.args) > 1:
            return self.args[1]

    def __repr__(self):
        match (self.head, self.tail):
            case None, None:
                return '[]'
            case head, None:
                return f'[{head}]'
            case head, Variable() as tail:
                return f'[{head}|{tail}]'
            case head, List(args=[]) as tail:
                return f'[{head}]'
            case head, List() as tail:
                # unwrap extra '[]'
                tail = re.sub(r'^\[(.+)\]$', r'\1', str(tail))
                return f'[{head},{tail}]'
            case head, tail:
                # List() is just a function so technically tail can be any type like an atom
                # e.g. [1|2] which is not a valid list but is syntactically correct
                return f'[{head}|{tail}]'

    @classmethod
    def from_list(cls, arr):
        if not arr:
            return cls()
        return cls(args=[arr[0], cls.from_list(arr[1:])])



class Predicate(Symbol):
    def __init__(self, name, args: list[Term]):
        self.name = name
        self.arity = len(args)
        self.args = args

    def __repr__(self):
        args = ', '.join([repr(arg) for arg in self.args])
        return f'{self.name}({args})'
    

class Cut(Predicate):
    def __init__(self):
        super().__init__(name="!", args=[])

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return '!'


class Rule:
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


def substitute(node: Symbol, assignment: dict):
    match node:
        case Cut() as cut:
            return cut
        case Predicate(name=name, args=args):
            args = [substitute(arg, assignment) for arg in args]
            return Predicate(name=name, args=args)
        case Variable() as v if v in assignment:
            while v in assignment:
                v = assignment[v]
            return v
        case Function(name=name, args=args) as function:
            args = [substitute(arg, assignment) for arg in args]
            T = type(function)
            return T(name=name, args=args)
        case _:
            return node


def relabel(rule: Rule):
    variables = {}
    def _relabel(node: None):
        match node:
            case Cut() as cut:
                return cut
            case Predicate(name=name, args=args):
                args = [_relabel(arg) for arg in args]
                return Predicate(name=name, args=args)
            case Variable(name=name) as v:
                if name not in variables:
                    variables[name] = Variable(name=name)
                return variables[name]
            case Function(name=name, args=args) as function:
                args = [_relabel(arg) for arg in args]
                T = type(function)
                return T(name=name, args=args)
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
        

def unify(x: Term | list[Term], y: Term | list[Term]):
    match (x, y):
        case (Atom(), Atom()) if x.name == y.name:
            return {}
        case (Function(), Function()) if x.name == y.name and x.arity == y.arity:
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
                if (new := unify(a, b)) is None:
                    return
                if (merged := merge(current, new)) is None:
                    return
                current = merged
            return simplify(current)


def merge(current, new):
    for variable, term in new.items():
        if variable in current:
            if (p := unify(current[variable], new[variable])) is None:
                return
            current = current | p            
        else:
            current = current | {variable: term}
    return current


def simplify(assignment):
    simplified = {}
    for variable, term in assignment.items():
        term = substitute(term, simplified)
        for v, t in simplified.items():
            simplified[v] = substitute(t, {variable: term})
        simplified[variable] = term
    return simplified


def get_cuts(stack):
    cuts = set()
    for pred in stack:
        if isinstance(pred, Cut):
            cuts.add(pred)
    return cuts


def query(stack: list[Predicate], rules: list[Rule], partial_assignment: list = [{}], stack_depth=0, cuts=set()):
    if not stack:
        # print("\tSolution:", partial_assignment)
        yield partial_assignment
        return

    print(stack_depth, "Current stack:", stack)
    predicate, stack = stack[0], stack[1:]
    # print('\t', predicate, stack)
    # print('\t', partial_assignment)
    # print()

    if isinstance(predicate, Cut):
        cuts.add(predicate)
        yield from query(stack, rules, partial_assignment, stack_depth+1, cuts | {predicate})
        return

    for rule in rules:
        print(stack_depth, get_cuts(stack), cuts, get_cuts(stack) & cuts)
        if (curr_cuts := get_cuts(stack)) and (curr_cuts & cuts):
            break

        rule = relabel(rule)
        if rule.head.name == predicate.name:
            print(stack_depth, "Trying to match", predicate, stack)
            pred, head = predicate.args, rule.head.args
            if (assignment := unify(pred, head)) is not None:
                print(stack_depth, "Unified:", predicate, rule.head, partial_assignment + [assignment])
                new_stack = [substitute(p, assignment) for p in stack]

                if not rule.body:
                    yield from query(new_stack, rules, partial_assignment + [assignment], stack_depth+1, cuts)
                else:
                    body = [substitute(p, assignment) for p in rule.body]
                    yield from query(body + new_stack, rules, partial_assignment + [assignment], stack_depth+1, cuts)
            else:
                pass
                print(stack_depth, "NOunify:", predicate, rule.head, partial_assignment)
