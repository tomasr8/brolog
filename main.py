from pathlib import Path
from prolog import Atom, Variable, Function, format_proof, query, unify, instantiate, QueryState
from parse import Parser


if __name__ == '__main__':
    a = Atom('a')
    b = Atom('b')
    f = Function('f', args=[a, b])
    X = Variable('X')
    Y = Variable('Y')
    Z = Variable('Z')
    g = Function('g', args=[Y, b])
    # A = [X]
    # B = [Function('s', args=[Variable('X')])]
    # relabel(A, B)
    # print(A, B)
    # print(unify(A, B, {'X': Atom('0')}))
    # print(unify([X, Z], [g, Y], {}))


    # r1 = Rule(head=Predicate('integer', args=[Atom('0')]))
    # r2 = Rule(head=Predicate('integer', args=[Function('s', args=[Variable('X')])]),
    #           body=[Predicate('integer', args=[Variable('X')])])
    # q = Predicate('integer', args=[Function('s', args=[Atom('0')])])
    # print(list(query([q], [r1, r2], {})))


    # X = Variable('X')
    # r1 = Rule(head=Predicate('list', args=[List()]))
    # r2 = Rule(head=Predicate('list', args=[List(head=Variable('_'),
    #                                             tail=X)]),
    #           body=[Predicate('list', args=[X])])
    # rules = [r1, r2]
    # print(r1)
    # print(r2)

    # L = List(head=Atom('1'), tail=List(head=Atom('2')))
    # q = Predicate('list', args=[L])
    # print(q)
    # proofs = list(query([q], rules))
    # print(proofs)
    # for proof in proofs:
    #     print(format_proof(q, rules, proof))


    # r1 = Rule(head=Predicate('p', args=[Atom('1'), Atom('2')]))
    # r2 = Rule(head=Predicate('p', args=[Atom('3'), Atom('3')]))
    # r3 = Rule(head=Predicate('p', args=[Atom('4'), Atom('5')]))

    # print(r1)
    # print(r2)
    # print(r3)

    # # q = Predicate('p', args=[Atom('3')])
    # N = Variable('N')
    # N2 = Variable('N')
    # q = Predicate('p', args=[N, N2])
    # print(q)
    # print(list(query([q], [r1, r2, r3])))

    source = Path('input.pl').read_text()
    p = Parser(source)
    rules = p.parse()
    for rule in rules:
        print(rule)

    # q = Parser('find(X, d, Path).').parse_head()
    # q = Parser('append([1,2], 3, L).').parse_head()
    # q = Parser('test(X, Y, Z).').parse_head()
    # q = Parser('int(s(s(0))).').parse_head()
    q = Parser('t(X).').parse_head()
    # q = Parser('p(X, Y, P).').parse_head()

    state = QueryState(rules, [q])
    tree = []

    proofs = list(query(state, tree))
    print(proofs)
    for proof in proofs:
        print(format_proof(q, rules, proof))
        print(f">> {instantiate(q, proof)}")

    print(tree)


    # print(List())
    # print(List(args=[Atom('a'), Atom('b')]))
    # print(List(args=[Atom('a'), Atom('b')]))
    # print(List(args=[Atom('a')]))
    # print(List(head=Atom('a'), tail=List(head=Variable('X'), tail=List(args=[Atom('d')]))))
    # print(List(head=Atom('a'), tail=Variable('X')))
    # print(List(head=Atom('a'), tail=List(head=Variable('X'))))

    # X = Variable('X')
    # p = unify(
    #     [X, X],
    #     [Atom('c'), Variable('Z')]
    # )
    # print(p)