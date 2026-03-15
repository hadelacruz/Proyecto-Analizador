from RegexParser import RegexParser

# Nodo del Árbol
class Node:
    _id_counter = 0
 
    def __init__(self, node_type: str, symbol=None, left=None, right=None):
        Node._id_counter += 1
        self.id = Node._id_counter
 
        self.type   = node_type
        self.symbol = symbol
        self.left   = left
        self.right  = right
 
        # Atributos calculados
        self.nullable: bool      = False
        self.firstpos: set[int]  = set()
        self.lastpos:  set[int]  = set()
        self.position: int|None  = None   # solo nodos LEAF
 
    def __repr__(self):
        if self.type == 'LEAF':
            sym = repr(self.symbol) if isinstance(self.symbol, str) else f"CLASS({len(self.symbol)})"
            return f"LEAF(pos={self.position}, sym={sym})"
        return f"{self.type}(nullable={self.nullable})"

class SyntaxTreeBuilder:
    def __init__(self, postfix: list):
        self.postfix = postfix
        self.position_map: dict[int, Node] = {}    # posición, nodo hoja
        self.followpos:    dict[int, set[int]] = {} # posición, conjunto de posiciones

    def build(self) -> Node:
        Node._id_counter = 0
        self.position_map.clear()
        self.followpos.clear()

        stack: list[Node] = []

        for item in self.postfix:
            tag, tok = item  # desempacar tupla 

            if tag == 'SYM':
                node = self._make_leaf(tok)
                stack.append(node)
                continue

            # tag == OP
            if tok == '·':
                right = stack.pop()
                left  = stack.pop()
                node  = Node('CONCAT', left=left, right=right)
                stack.append(node)

            elif tok == '|':
                right = stack.pop()
                left  = stack.pop()
                node  = Node('OR', left=left, right=right)
                stack.append(node)

            elif tok == '*':
                child = stack.pop()
                node  = Node('STAR', left=child)
                stack.append(node)

            elif tok == '+':
                r = stack.pop()
                star_r = Node('STAR', left=r)
                stack.append(Node('CONCAT', left=r, right=star_r))

            elif tok == '?':
                r = stack.pop()
                eps = Node('EPSILON')
                stack.append(Node('OR', left=r, right=eps))

            else:
                raise ValueError(f"Unknown operator in postfix: {tok!r}")

        if not stack:
            raise ValueError("Empty postfix expression.")

        root = stack[-1]
        self._compute_attributes(root)
        self._compute_followpos(root)
        return root

    # Creación de hojas
    def _make_leaf(self, value) -> Node:
        pos = len(self.position_map) + 1
        node = Node('LEAF', symbol=value)
        node.position = pos
        self.position_map[pos] = node
        self.followpos[pos] = set()
        return node


    # Cálculo de atributos nullable, firstpos, lastpos  
    def _compute_attributes(self, node: Node):
        if node is None:
            return

        self._compute_attributes(node.left)
        self._compute_attributes(node.right)

        if node.type == 'LEAF':
            node.nullable = False
            node.firstpos = {node.position}
            node.lastpos  = {node.position}

        elif node.type == 'EPSILON':
            node.nullable = True
            node.firstpos = set()
            node.lastpos  = set()

        elif node.type == 'OR':
            node.nullable = node.left.nullable or node.right.nullable
            node.firstpos = node.left.firstpos | node.right.firstpos
            node.lastpos  = node.left.lastpos  | node.right.lastpos

        elif node.type == 'CONCAT':
            node.nullable = node.left.nullable and node.right.nullable
            if node.left.nullable:
                node.firstpos = node.left.firstpos | node.right.firstpos
            else:
                node.firstpos = node.left.firstpos
            if node.right.nullable:
                node.lastpos = node.left.lastpos | node.right.lastpos
            else:
                node.lastpos = node.right.lastpos

        elif node.type == 'STAR':
            node.nullable = True
            node.firstpos = node.left.firstpos
            node.lastpos  = node.left.lastpos


    # Cálculo de Followpos
    def _compute_followpos(self, node: Node):
        if node is None:
            return

        if node.type == 'CONCAT':
            # Para cada posición i en lastpos(left)
            for pos in node.left.lastpos:
                self.followpos[pos] |= node.right.firstpos

        elif node.type in 'STAR':
            # Para cada posición i en lastpos(node)
            for pos in node.lastpos:
                self.followpos[pos] |= node.firstpos

        self._compute_followpos(node.left)
        self._compute_followpos(node.right)


if __name__ == "__main__":
    test_regex = "('a'|'b')*'a''b''b''#'"
    print(f"Regex: {test_regex}")

    parser = RegexParser(test_regex)
    postfix = parser.to_postfix()
    print(f"Postfix: {postfix}")

    builder = SyntaxTreeBuilder(postfix)
    root = builder.build()

    print(f"\nRoot: {root}")
    print(f"  nullable  = {root.nullable}")
    print(f"  firstpos  = {root.firstpos}")
    print(f"  lastpos   = {root.lastpos}")

    print("\nPosition map:")
    for pos, leaf in builder.position_map.items():
        print(f"  pos {pos}: symbol={leaf.symbol!r}")

    print("\nFollowpos:")
    for pos, fp in builder.followpos.items():
        print(f"  followpos({pos}) = {fp}")
