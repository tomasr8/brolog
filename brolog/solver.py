import itertools
from collections.abc import Callable, Generator
from dataclasses import dataclass, field, fields
from typing import Self

from brolog.objects import Atom, Cut, Function, Predicate, Rule, Symbol, Term, Variable
from brolog.parse import Parser


try:
    import networkx as nx
except ImportError:
    nx = None


def contains(term: Term, x: Variable) -> bool:
    match term:
        case Variable() as y:
            return x == y
        case Function(args=args):
            return any(contains(arg, x) for arg in args)
        case _:
            return False


def substitute(node: Symbol, substitution: dict[Variable, Term] | Callable[[Variable], Variable]) -> Symbol:
    """
    Replace all variables in a symbol (predicate or term) with its corresponding value.

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
        case Function(name=name, args=args) as f:
            args = [substitute(arg, substitution) for arg in args]
            return type(f)(name=name, args=args)
        case Variable() as v:
            if callable(substitution):
                return substitution(v)
            while v in substitution:
                v = substitution[v]
            if isinstance(v, Function):
                v = substitute(v, substitution)
            return v


def relabel(rule: Rule) -> Rule:
    variables = {}

    def _relabel(v: Variable) -> Variable:
        if v not in variables:
            variables[v] = Variable(v.name)
        return variables[v]

    return Rule(
        head=substitute(rule.head, _relabel),
        body=[substitute(p, _relabel) for p in rule.body],
    )


def unify(x: Symbol | list[Term], y: Symbol | list[Term]) -> dict[Variable, Term] | None:  # noqa: PLR0911
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
            return {x: y}
        case (Variable(), (Atom() | Function()) as term):
            if not contains(term, x):
                return {x: term}
        case ((Atom() | Function()) as term, Variable()):
            if not contains(term, y):
                return {y: term}
        case (list(), list()) if len(x) == len(y):
            current = {}
            for a, b in zip(x, y, strict=True):
                asub = substitute(a, current)
                bsub = substitute(b, current)

                if (new := unify(asub, bsub)) is None:
                    return None
                current |= new
            return current


def instantiate(pred: Predicate, assignments: list[dict[Variable, Term]]) -> Predicate:
    for assignment in assignments:
        pred = substitute(pred, assignment)
    return pred


def get_variable_assignments(q: Predicate, assignments: list[dict[Variable, Term]]) -> dict[Variable, Term]:
    return {v: instantiate(v, assignments) for v in get_variables(q)}


def get_variables(symbol: Symbol) -> list[Variable]:
    def _get_variables(symbol: Symbol) -> list[Variable]:
        match symbol:
            case Atom():
                return []
            case Variable() as v:
                return [v]
            case Function(args=args) | Predicate(args=args):
                return itertools.chain.from_iterable(_get_variables(arg) for arg in args)

    return list(dict.fromkeys(_get_variables(symbol)))


def get_cuts(stack: list[Predicate]) -> set[Cut]:
    return {pred for pred in stack if isinstance(pred, Cut)}


def cut_active(stack: list[Predicate], cuts: set[Cut]) -> bool:
    return any(cut in cuts for cut in get_cuts(stack))


@dataclass
class QueryState:
    rules: list[Rule]
    stack: list[Predicate]
    search_depth: int = 0
    active_cuts: set[Cut] = field(default_factory=set)
    variable_assignments: list[dict[Variable, Term]] = field(default_factory=list)

    def make_new(self, **kwargs) -> Self:
        # asdict() creates a deep copy but wee need to preserve the original objects
        values = {field.name: getattr(self, field.name) for field in fields(self)}
        kwargs = values | {"search_depth": self.search_depth + 1} | kwargs
        return QueryState(**kwargs)


@dataclass
class SearchTree:
    stack: list[Predicate]
    search_depth: int = 0
    variable_assignments: list[dict[Variable, Term]] = field(default_factory=list)
    children: list[Self] = field(default_factory=list)

    @classmethod
    def from_query_state(cls: type[Self], state: QueryState) -> Self:
        return cls(
            stack=state.stack,
            search_depth=state.search_depth,
            variable_assignments=state.variable_assignments,
        )

    if nx is not None:
        from networkx import DiGraph

        def to_networkx_graph(self) -> DiGraph:
            G = nx.DiGraph()
            self._make_graph(G)
            # Draw to a PDF file using Graphviz
            # A = nx.drawing.nx_agraph.to_agraph(G)  # noqa: ERA001
            # A.draw("somegraph3.pdf", prog="dot", args="-Grankdir=TB")  # noqa: ERA001
            return G

        def _make_graph(self, G: DiGraph) -> None:
            for child in self.children:
                G.add_edge(str(self.stack), str(child.stack), label=str(child.variable_assignments))
                self._make_graph(G, child)


def query(
    rules: list[Predicate] | str, q: Predicate | str, *, with_search_tree: bool = False
) -> (
    Generator[list[dict[Variable, Term]], None, None]
    | tuple[Generator[list[dict[Variable, Term]], None, None], SearchTree]
):
    if isinstance(rules, str):
        rules = Parser(rules).parse()
    if isinstance(q, str):
        q = Parser(q).parse(head_only=True)

    state = QueryState(rules, [q])
    search_tree = SearchTree([q])

    if with_search_tree:
        return _query(state, search_tree), search_tree
    return _query(state, search_tree)


def _query(state: QueryState, search_tree: SearchTree) -> Generator[list[dict[Variable, Term]], None, None]:
    tree_node = SearchTree.from_query_state(state)
    search_tree.children.append(tree_node)

    # If the stack is empty, we have proven the query
    if not state.stack:
        yield state.variable_assignments
        return

    predicate, stack = state.stack[0], state.stack[1:]

    if isinstance(predicate, Cut):
        # Activate the cut for the current branch
        state.active_cuts.add(predicate)
        yield from _query(
            state.make_new(stack=stack),
            tree_node,
        )
        return

    skip_alternatives = False
    for rule in state.rules:
        # If there is an active cut, we must not bactrack beyond the active cut
        if cut_active(stack, state.active_cuts):
            break

        # If we activated a cut when evaluating a branch, we must not evaluate any alternatives
        if skip_alternatives:
            break

        rule = relabel(rule)  # noqa: PLW2901
        if (assignment := unify(predicate, rule.head)) is None:
            continue

        # Apply the unification assignments to the stack
        new_stack = [substitute(p, assignment) for p in stack]

        if not rule.body:
            yield from _query(
                state.make_new(
                    stack=new_stack,
                    variable_assignments=[*state.variable_assignments, assignment],
                ),
                tree_node,
            )
        else:
            body = [substitute(p, assignment) for p in rule.body]
            cuts = get_cuts(body)
            yield from _query(
                state.make_new(
                    stack=body + new_stack,
                    variable_assignments=[*state.variable_assignments, assignment],
                ),
                tree_node,
            )
            if state.active_cuts & cuts:
                # A cut which is on the stack was activated in a previous branch,
                # We must not evaluate any alternatives
                skip_alternatives = True
            # Deactivate cuts when leaving this branch
            for cut in cuts:
                state.active_cuts.discard(cut)
