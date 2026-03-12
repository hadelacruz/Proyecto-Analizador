import re
from SpecParser import TokenSpec

class MacroExpander:
    def __init__(self, tokens: list[TokenSpec], macros: dict[str, str]):
        self.tokens = tokens
        self.macros = macros
        self._expanded_cache: dict[str, str] = {}

    # Expande todos los macros en las regex de los tokens
    def expand(self) -> list[TokenSpec]:
        expanded_tokens = []
        for token in self.tokens:
            new_regex = self._expand_regex(token.regex)
            expanded_tokens.append(TokenSpec(
                name=token.name,
                regex=new_regex,
                priority=token.priority
            ))
        return expanded_tokens

    # Expande recursivamente los macros
    def _expand_regex(self, regex: str) -> str:
        for _ in range(100):
            new_regex = self._single_pass(regex)
            if new_regex == regex:
                break
            regex = new_regex
        return regex

    # Reemplaza una sola vez los macros en la regex
    def _single_pass(self, regex: str) -> str:
        def replace_braced(m):
            name = m.group(1)
            if name in self.macros:
                return f"({self._get_expanded(name)})"
            return m.group(0)

        regex = re.sub(r'\{([A-Za-z_][A-Za-z0-9_]*)\}', replace_braced, regex)

        result = []
        i = 0
        while i < len(regex):
            if regex[i] == "'" and i + 2 < len(regex) and regex[i + 2] == "'":
                result.append(regex[i:i+3])
                i += 3
                continue

            if regex[i] == '"':
                j = i + 1
                while j < len(regex) and regex[j] != '"':
                    j += 1
                result.append(regex[i:j+1])
                i = j + 1
                continue

            if regex[i] == '[':
                j = i + 1
                while j < len(regex) and regex[j] != ']':
                    j += 1
                result.append(regex[i:j+1])
                i = j + 1
                continue

            m = re.match(r'([A-Za-z_][A-Za-z0-9_]*)', regex[i:])
            if m:
                word = m.group(1)
                if word in self.macros:
                    result.append(f"({self._get_expanded(word)})")
                    i += len(word)
                    continue

            result.append(regex[i])
            i += 1

        return ''.join(result)

    # Evita expandir el mismo macro varias veces
    def _get_expanded(self, name: str) -> str:
        if name in self._expanded_cache:
            return self._expanded_cache[name]

        raw = self.macros.get(name, name)
        expanded = self._expand_regex(raw)
        self._expanded_cache[name] = expanded
        return expanded


if __name__ == "__main__":
    from SpecParser import SpecParser
    import sys

    if len(sys.argv) < 2:
        print("Usage: python MacroExpander.py <file.yal>")
        sys.exit(1)

    parser = SpecParser(sys.argv[1])
    tokens, macros = parser.parse()

    expander = MacroExpander(tokens, macros)
    expanded = expander.expand()

    print("\nTOKENS EXPANDIDOS\n")
    for t in expanded:
        print(f"  {t}")
