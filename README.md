## Brolog - Prolog interpreter written in Python

### Installation

```bash
pip install brolog
```

### CLI usage

```bash
brolog input.pl
```

```prolog
?- list([]).
true.

?- list([1,2]).
true.

?- append(X, Y, [1,2,3]).
X = [1,2],
Y = 3.

?- append([1], X, [4,5]).
false.

```

Using this file as input:

```prolog
list([]).
list([_|T]) :- list(T).

append([], X, [X]).
append([H|T], X, [H|R]) :- append(T, X, R).
```

### Supported builtins

- Lists: `[H|T]`, `[1,2]`, ..
- Cut: `!`
- Arbitrary symbolic functions: `f()`, `g(a, b)`, ..

### TODO

- (WIP) Use networkx to generate the SDL tree of a query
- Add more commonly used builtins
