import networkx as nx


def draw_graph():
    G = nx.DiGraph()
    G.add_edge('path(X, Y)', 'path(X, X)', label='{X → Y}')
    G.add_edge('path(X, X)', '[]')
    G.add_edge('path(X, Y)', 'e(X, Z), path(Z, Y)')
    G.add_edge('e(X, Z), path(Z, Y)', 'path(b, Y)', label='{X → a, Y → b}')


    # G.add_nodes_from([r'α', r'β'])
    A = nx.drawing.nx_agraph.to_agraph(G)
    A.draw('somegraph2.pdf', prog='dot', args="-Grankdir=TB")


draw_graph()
