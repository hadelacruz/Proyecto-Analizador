from SpecParser import TokenSpec


# Usamos caracteres Unicode privados como marcadores únicos para cada token.
END_MARKER = '\x00'


class RegexUnifier:
    def __init__(self, tokens: list[TokenSpec]):
        #  Lista de tokens con regex ya expandidas
        self.tokens = tokens
        # Mapa de marcadores a tokens para identificar qué token corresponde a cada rama en la regex unificada
        self.marker_to_token: dict[str, TokenSpec] = {}

    def unify(self) -> tuple[str, dict[str, TokenSpec]]:
        branches = []

        for token in self.tokens:
            # Crea un marcador único para este token basado en su prioridad
            marker = chr(0xE000 + token.priority)
            self.marker_to_token[marker] = token

            # Envuelve la regex del token en un grupo y añade el marcador al final
            branch = f"({token.regex}){marker}"
            branches.append(branch)

        unified = '|'.join(branches)
        return unified, self.marker_to_token


if __name__ == "__main__":
    from SpecParser import SpecParser
    from MacroExpander import MacroExpander
    import sys

    if len(sys.argv) < 2:
        print("Usage: python RegexUnifier.py <file.yal>")
        sys.exit(1)

    parser = SpecParser(sys.argv[1])
    tokens, macros = parser.parse()

    expander = MacroExpander(tokens, macros)
    expanded = expander.expand()

    unifier = RegexUnifier(expanded)
    unified, marker_map = unifier.unify()

    print("=== UNIFIED REGEX ===")
    print(unified)
    print("\n=== MARKER MAP ===")
    for marker, token in marker_map.items():
        print(f"  U+{ord(marker):04X} → {token.name}")
