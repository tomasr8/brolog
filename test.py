

class Node:
    pass


class Atom(Node):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name



a = Atom('a')
b = Atom('b')


match (a, b):
    case (Atom(name=name_a), Atom(name=name_b)) if name_b == name_b:
        print(name_a)
    case _:
        print("rip")