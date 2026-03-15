from SpecParser import TokenSpec

ACCEPT_MARKER = '#'


class RegexUnifier:
    def __init__(self, tokens: list[TokenSpec]):
        #  Lista de tokens con regex ya expandidas
        self.tokens = tokens

    def unify(self) -> tuple[str, dict[str, TokenSpec]]:
        branches = []

        for token in self.tokens:
            # Envuelve la regex del token en un grupo y añade el marcador al final
            branch = f"({token.regex}){ACCEPT_MARKER}"
            branches.append(branch)

        unified = '|'.join(branches)
        return unified, list(self.tokens)


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
    unified, tokensUnified = unifier.unify()

    print("UNIFIED REGEX")
    print(unified)
    print("\nMARKER MAP")
    for token in tokensUnified:
        print(f"  {token.name}")
