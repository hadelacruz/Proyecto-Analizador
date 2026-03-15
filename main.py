"""
main.py — Punto de entrada del Generador de Analizadores Léxicos
Uso:
    python main.py <input.yal> [-o lexer.py] [--tree]
"""

import sys
import argparse

from SpecParser            import SpecParser
from MacroExpander         import MacroExpander
from RegexUnifier          import RegexUnifier, build_marker_map
from RegexParser           import RegexParser
from SyntaxTreeBuilder     import SyntaxTreeBuilder
from DirectDFAConstructor  import DirectDFAConstructor
from CodeGenerator         import CodeGenerator
from TreeVisualizer        import draw_tree


def run(yal_path: str, output_path: str = "lexer.py", render_tree: bool = False):
    print(f"  Generador de Analizadores Léxicos")
    print(f"  Entrada: {yal_path}")
    print(f"  Salida: {output_path}")

    # 1. Parsear el .yal
    print("1. Parseando archivo .yal")
    spec_parser = SpecParser(yal_path)
    tokens, macros = spec_parser.parse()
    print(f"      {len(macros)} macros, {len(tokens)} reglas de token.")

    if not tokens:
        print("ERROR: No se encontraron reglas de token en el archivo .yal.")
        sys.exit(1)

    # 2. Expandir macros
    print("2. Expandiendo macros")
    expander = MacroExpander(tokens, macros)
    expanded_tokens = expander.expand()
    for t in expanded_tokens:
        print(f"      {t.name:20s} -> {t.regex[:70]}")

    # 3. Unificar regexes
    print("3. Unificando regex")
    unifier = RegexUnifier(expanded_tokens)
    unified, tok_ordered = unifier.unify()
    print(f"      Regex unificada: {len(unified)} caracteres")

    # 4. Convertir a postfijo con regex aumentada '#'
    print("4. Convirtiendo a postfix")
    postfix = RegexParser(unified).to_postfix()
    print(f"      Longitud postfix: {len(postfix)} tokens")

    # 5. Construir árbol sintáctico
    print("5. Construyendo árbol sintáctico")
    builder = SyntaxTreeBuilder(postfix)
    root = builder.build()
    print(f"      Posiciones en el árbol : {len(builder.position_map)}")
    print(f"      firstpos de la raíz    : {root.firstpos}")

    # Construir mapa posición -> TokenSpec 
    marker_map = build_marker_map(builder.position_map, tok_ordered)
    print(f"      Marcadores '#' mapeados: {list(marker_map.items())}")

    # 5b. Renderizar árbol puede ser opcional
    if render_tree:
        print("\n5.1 Renderizando árbol sintáctico")
        draw_tree(root, './img/syntax_tree')

    # 6. Construir y minimizar AFD
    print("6 Construyendo y minimizando AFD")
    constructor = DirectDFAConstructor(
        root, builder.followpos, builder.position_map, marker_map
    )
    constructor.build()
    constructor.minimize()
    print(f"      Estados AFD minimizado: {len(constructor.states)}")
    for s in constructor.states:
        if s.is_accepting:
            print(f"        estado aceptante -> {s.token_name}")

    # 7. Generar código
    print("\n7. Generando código del lexer")
    CodeGenerator(
        states = constructor.states,
        start_state = constructor.start_state,
        header = spec_parser.header,
        trailer = spec_parser.trailer,
    ).generate(output_path)

    print(f"\n Lexer guardado en: {output_path}\n")


def main():
    parser = argparse.ArgumentParser(description="Generador de Analizadores Léxicos YALex")
    parser.add_argument("yal_file")
    parser.add_argument("-o", "--output", default="lexer.py")
    parser.add_argument("--tree", action="store_true", help="Renderizar el árbol sintáctico (requiere graphviz)")
    args = parser.parse_args()
    run(args.yal_file, args.output, args.tree)


if __name__ == "__main__":
    main()