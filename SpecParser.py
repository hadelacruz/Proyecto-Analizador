import sys
import re

class TokenSpec:
    def __init__(self, name: str, regex: str, priority: int):
        self.name = name
        self.regex = regex
        self.priority = priority

    def __repr__(self):
        return f"TOKEN({self.name}, priority={self.priority}, regex={self.regex!r})"

# Parsear archivos .yal
class SpecParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.macros: dict[str, str] = {}
        self.tokens: list[TokenSpec] = []
        self.header: str = ""
        self.trailer: str = ""

    # Devuelve los tokens y los macros encontrados
    def parse(self) -> tuple[list[TokenSpec], dict[str, str]]:
        with open(self.filepath, "r", encoding="utf-8") as f:
            source = f.read()

        source = self._remove_comments(source)
        source = self._extract_header_trailer(source)
        self._parse_let_definitions(source)
        self._parse_rules(source)

        return self.tokens, self.macros

    # Remover los comentarios del .yal
    def _remove_comments(self, source: str) -> str:
        return re.sub(r'\(\*.*?\*\)', '', source, flags=re.DOTALL)

    # Extraer el header y el trailer
    def _extract_header_trailer(self, source: str) -> str:
        first_keyword = re.search(r'\b(let|rule)\b', source)
        search_area = source[:first_keyword.start()] if first_keyword else source

        header_match = re.search(r'\{(.*?)\}', search_area, re.DOTALL)
        if header_match:
            self.header = header_match.group(1).strip()
            source = source[:header_match.start()] + source[header_match.end():]

        rule_match = re.search(r'\brule\b', source)
        if rule_match:
            after_rule = source[rule_match.start():]
            all_braces = list(re.finditer(r'\{[^{}]*\}', after_rule))
            if len(all_braces) >= 2:
                last = all_braces[-1]

                before_last = after_rule[:last.start()].rstrip()
                if before_last.endswith('}'):
                    self.trailer = last.group(1).strip()
                    end = rule_match.start() + last.start()
                    source = source[:end]

        return source

    # Parsear las definiciones de let
    def _parse_let_definitions(self, source: str):

        rule_start = re.search(r'\brule\b', source)
        let_block = source[:rule_start.start()] if rule_start else source

        pattern = re.compile(
            r'\blet\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)(?=\blet\b|\Z)',
            re.DOTALL
        )
        for match in pattern.finditer(let_block):
            name = match.group(1).strip()
            regex = match.group(2).strip()
            self.macros[name] = regex

    # Parsear las reglas de token
    def _parse_rules(self, source: str):
        rule_match = re.search(r'\brule\s+\w+\s*=\s*(.*)', source, re.DOTALL)
        if not rule_match:
            raise ValueError("No 'rule' block found in .yal file.")

        rules_body = rule_match.group(1).strip()

        branches = self._split_branches(rules_body)

        priority = 1
        for branch in branches:
            branch = branch.strip()
            if not branch:
                continue

            action_match = re.search(r'\{([^{}]*)\}', branch)
            if not action_match:
                continue

            action = action_match.group(1).strip()
            regex = branch[:action_match.start()].strip()

            name = self._extract_token_name(action)

            token = TokenSpec(
                name=name,
                regex=regex,
                priority=priority
            )
            self.tokens.append(token)
            priority += 1

    # Dividir el cuerpo de las reglas por '|'
    def _split_branches(self, body: str) -> list[str]:
        branches = []
        current = []
        depth_paren = 0
        depth_bracket = 0
        in_single_quote = False
        in_double_quote = False
        i = 0

        while i < len(body):
            c = body[i]

            if c == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif c == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif not in_single_quote and not in_double_quote:
                if c == '(':
                    depth_paren += 1
                elif c == ')':
                    depth_paren -= 1
                elif c == '[':
                    depth_bracket += 1
                elif c == ']':
                    depth_bracket -= 1
                elif c == '|' and depth_paren == 0 and depth_bracket == 0:
                    branches.append(''.join(current))
                    current = []
                    i += 1
                    continue

            current.append(c)
            i += 1

        if current:
            branches.append(''.join(current))

        return branches

    # Extraer el nombre del token a partir de la acción
    def _extract_token_name(self, action: str) -> str:

        m = re.search(r'return\s+([A-Z_][A-Z0-9_]*)', action)
        if m:
            return m.group(1)

        m = re.search(r'return\s+(\w+)', action)
        if m:
            return m.group(1).upper()

        if 'raise' in action.lower():
            return 'EOF'

        return re.sub(r'\W+', '_', action).upper()[:20]


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python SpecParser.py <file.yal>")
        sys.exit(1)

    parser = SpecParser(sys.argv[1])
    tokens, macros = parser.parse()

    print("MACROS\n")
    for name, regex in macros.items():
        print(f"  {name} = {regex!r}")

    print("\nTOKENS\n")
    for t in tokens:
        print(f"  {t}")

    if parser.header:
        print(f"\nHEADER\n{parser.header}")
    else:
        print("\nNo HEADER found.")
    if parser.trailer:
        print(f"\nTRAILER\n{parser.trailer}")
    else:
        print("\nNo TRAILER found.")
