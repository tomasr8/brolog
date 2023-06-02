parent(george, elizabeth).
test([T|R]) :- R = 3.
p(L2) :- test(L), append(L, 2, L2).

r([X|2]) :- X = 3.