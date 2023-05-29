# list([]).
# list([_|X]) :- list(X).

p(1, 2).
p(3, 3).
p(4, 5).

e(a, b).
e(b, c).
e(c, d).

path(X, X).
path(X, Y) :- e(X, Z), path(Z, Y).

find(X, X, []).
find(X, Y, [Z|T]) :- e(X, Z), find(Z, Y, T).

# append([], X, [X]).
# append([H|T], X, [H|R]) :- append(T, X, R).

# t(3).
# t(D, D).
# test([H|Z], [T, R], R) :- t(R), t([T, R], Z).

# [T|R] [T,[R]]
# [H|R], R = X, 3
# array(H, R), R = X, 3
# array(H, 3)

# int(0).
# int(s(X)) :- int(X).

# add(0, X, X).
# add(s(X), Y, s(Z)) :- add(X, Y, Z).


# g(1).
# g(2).
# h(1).
# t(X) :- g(X), !, !, h(X).


# r(a, b).
# r(b, c).
# r(c, d).
# r(a, f).
# r(b, f).
# p(X, X, a()).
# p(X, Z, a(Y, P)) :- r(X, Y), p(Y, Z, P), !.


















