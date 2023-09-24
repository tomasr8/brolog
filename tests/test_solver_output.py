import json
from pathlib import Path

import pytest

from brolog.parse import Parser
from brolog.solver import QueryState, SearchTree, _query, instantiate


test_cases = [
    {
        "name": "list",
        "program": """\
list([]).
list([_|X]) :- list(X).""",
        "queries": [
            "list([]).",
            "list([a]).",
            "list([a, b, c]).",
            "list(a).",
        ],
    },
    {
        "name": "append",
        "program": """\
append([], X, [X]).
append([H|T], X, [H|R]) :- append(T, X, R).""",
        "queries": [
            "append([1, 2], 3, [1, 2, 3]).",
            "append([1], X, [1, 2]).",
            "append([X, Y], 3, [1, 2, 3]).",
            "append([1, 2], 3, X).",
        ],
    },
    {
        "name": "transitivity",
        "program": """\
e(a, b).
e(b, c).
e(c, d).
path(X, X).
path(X, Y) :- e(X, Z), path(Z, Y).
find(X, X, []).
find(X, Y, [Z|T]) :- e(X, Z), find(Z, Y, T).""",
        "queries": [
            "path(a, d).",
            "path(a, a).",
            "path(a, Y).",
            "path(X, d).",
            "find(a, d, Path).",
            "find(a, a, Path).",
            "find(a, X, Path).",
        ],
    },
    {
        "name": "cut",
        "program": """\
g(1).
g(2).
h(1).
t(X) :- g(X), !, h(X).""",
        "queries": [
            "t(1).",
            "t(2).",
            "t(3).",
            "t(X).",
        ],
    },
    {
        "name": "list-member",
        "program": """\
list_member(X,[X|_]) :- !.
list_member(X,[_|TAIL]) :- list_member(X,TAIL).
""",
        "queries": [
            "list_member(1, [2]).",
            "list_member(2, [2, 2]).",
            "list_member(2, [2, 2, 2]).",
            "list_member(2, [1, 2]).",
            "list_member(X, [1, 2]).",
        ],
    },
]


@pytest.mark.parametrize("test_case", test_cases)
def test_solver_output(snapshot, test_case):
    name = test_case["name"]
    snapshot_dir = Path(__file__).parent / "data"
    path = snapshot_dir / f"{name}.json"

    rules = Parser(test_case["program"]).parse()
    answers = []
    for _q in test_case["queries"]:
        q = Parser(_q).parse_head()
        state = QueryState(rules, [q])

        proofs = list(_query(state, SearchTree([q])))
        answers.append([str(instantiate(q, proof)) for proof in proofs])

    snapshot.snapshot_dir = snapshot_dir
    snapshot.assert_match(json.dumps(answers, indent=2), path)
