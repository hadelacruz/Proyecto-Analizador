from SyntaxTreeBuilder import Node
from graphviz import Digraph


def draw_tree(root: Node, filename: str = "syntax_tree"):
    dot = Digraph(comment="Syntax Tree", format="png")

    # Configuración global del grafo
    dot.attr(
        rankdir="TB",
        bgcolor="white",
        nodesep="0.4",
        ranksep="0.6"
    )

    # Estilo global de nodos
    dot.attr(
        "node",
        fontname="Helvetica",
        fontsize="11",
        shape="ellipse",
        style="filled",
        color="#2c3e50",
        penwidth="1.2"
    )

    # Estilo de aristas
    dot.attr(
        "edge",
        color="#34495e",
        arrowsize="0.7",
        penwidth="1.1"
    )

    dot.attr(splines="ortho")
    dot.attr(ranksep="1.0")
    dot.attr(nodesep="0.6")

    _visit_tree(root, dot)

    dot.render(filename, cleanup=True)
    print(f"Árbol sintáctico generado: {filename}.png")


def _visit_tree(node: Node, dot: Digraph):
    if node is None:
        return

    node_id = str(node.id)
    label = _tree_node_label(node)

    # Estilos por tipo de nodo
    if node.type == "LEAF":
        dot.node(
            node_id,
            label,
            shape="box",
            fillcolor="#FFF3B0",
            style="filled,rounded"
        )

    elif node.type in ("CONCAT", "OR"):
        dot.node(
            node_id,
            label,
            fillcolor="#A8DADC"
        )

    elif node.type == "STAR":
        dot.node(
            node_id,
            label,
            fillcolor="#B7E4C7"
        )

    elif node.type == "EPSILON":
        dot.node(
            node_id,
            label,
            shape="box",
            fillcolor="#E0E0E0",
            style="filled,rounded"
        )

    else:
        dot.node(node_id, label)

    if node.left:
        dot.edge(node_id, str(node.left.id))
        _visit_tree(node.left, dot)

    if node.right:
        dot.edge(node_id, str(node.right.id))
        _visit_tree(node.right, dot)


def _tree_node_label(node: Node) -> str:

    if node.type == "LEAF":
        if isinstance(node.symbol, set):
            sym_repr = compress_char_set(node.symbol)
        elif node.symbol == "#":
            sym_repr = "#"
        elif ord(node.symbol) >= 0xE000:
            sym_repr = "END"
        else:
            sym_repr = repr(node.symbol)

        return f"{sym_repr}\npos={node.position}\nnull={node.nullable}"

    elif node.type == "EPSILON":
        return "ε\nnull=True"

    op_symbols = {
        "CONCAT": "·",
        "OR": "|",
        "STAR": "*"
    }

    op = op_symbols.get(node.type, node.type)

    return (
        f"{op}\n"
        f"null={node.nullable}\n"
        f"fp={node.firstpos}\n"
        f"lp={node.lastpos}"
    )

def compress_char_set(chars):
    chars = sorted(chars)

    if len(chars) > 2 and ord(chars[-1]) - ord(chars[0]) + 1 == len(chars):
        return f"[{chars[0]}-{chars[-1]}]"

    return "[" + "".join(chars[:6]) + ("..." if len(chars) > 6 else "") + "]"
 