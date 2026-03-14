from RegexParser import RegexParser

def expand_char_class(class_token: str) -> set[str]:
    inner = class_token[1:-1].strip()   # eliminar  y
    negated = inner.startswith('^')
    if negated:
        inner = inner[1:].strip()

    chars = set()
    i = 0
    tokens = _tokenize_class_inner(inner)

    j = 0
    while j < len(tokens):
        if j + 2 < len(tokens) and tokens[j+1] == '-':
            # rango
            start = tokens[j]
            end   = tokens[j+2]
            for code in range(ord(start), ord(end) + 1):
                chars.add(chr(code))
            j += 3
        else:
            chars.add(tokens[j])
            j += 1

    if negated:
        all_chars = set(chr(i) for i in range(32, 127))
        chars = all_chars - chars

    return chars


def _tokenize_class_inner(inner: str) -> list[str]:
    tokens = []
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == "'":
            if i + 1 < len(inner) and inner[i+1] == '\\':
                escape_map = {'n': '\n', 't': '\t', 'r': '\r',
                              '\\': '\\', "'": "'"}
                ch = escape_map.get(inner[i+2], inner[i+2])
                tokens.append(ch)
                i += 4  
            else:
                tokens.append(inner[i+1])
                i += 3  
        elif c == '-':
            tokens.append('-')
            i += 1
        elif c in ' \t':
            i += 1
        else:
            tokens.append(c)
            i += 1
    return tokens

# Nodo del Árbol
class Node:
    _id_counter = 0

    def __init__(self, node_type: str, symbol=None, left=None, right=None):
        Node._id_counter += 1
        self.id = Node._id_counter

        self.type     = node_type
        self.symbol   = symbol          # str o set para LEAF
        self.left     = left
        self.right    = right

        # Atributos calculados por SyntaxTreeBuilder
        self.nullable:  bool       = False
        self.firstpos:  set[int]   = set()
        self.lastpos:   set[int]   = set()
        self.position:  int | None = None   # solo para nodos LEAF

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

            elif tok == '#':
                right = stack.pop()
                left  = stack.pop()
                node  = Node('DIFF', left=left, right=right)
                stack.append(node)

            elif tok == '*':
                child = stack.pop()
                node  = Node('STAR', left=child)
                stack.append(node)

            elif tok == '+':
                child = stack.pop()
                node  = Node('PLUS', left=child)
                stack.append(node)

            elif tok == '?':
                child = stack.pop()
                node  = Node('QUESTION', left=child)
                stack.append(node)

            else:
                raise ValueError(f"Unknown operator in postfix: {tok!r}")

        if not stack:
            raise ValueError("Empty postfix expression.")

        root = stack[-1]
        self._compute_attributes(root)
        self._compute_followpos(root)
        return root

    # Creación de hojas
    def _make_leaf(self, tok: str) -> Node:
        position = len(self.position_map) + 1

        if tok.startswith('['):
            symbol = expand_char_class(tok)
        elif tok == 'eof':
            symbol = '\x03'   # ETX como marcador EOF
        else:
            symbol = tok      # carácter único

        node = Node('LEAF', symbol=symbol)
        node.position = position
        self.position_map[position] = node
        self.followpos[position] = set()
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

        elif node.type == 'PLUS':
            node.nullable = node.left.nullable
            node.firstpos = node.left.firstpos
            node.lastpos  = node.left.lastpos

        elif node.type == 'QUESTION':
            node.nullable = True
            node.firstpos = node.left.firstpos
            node.lastpos  = node.left.lastpos

        elif node.type == 'DIFF':
            # A # B    A para propósitos DFA simplificado
            node.nullable = node.left.nullable
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

        elif node.type in ('STAR', 'PLUS'):
            # Para cada posición i en lastpos(node)
            for pos in node.lastpos:
                self.followpos[pos] |= node.firstpos

        self._compute_followpos(node.left)
        self._compute_followpos(node.right)


if __name__ == "__main__":
    test_regex = "('a'|'b')*'a''b''b'"
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
