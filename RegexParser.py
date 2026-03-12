
class Sym:
    __slots__ = ('value',)
    def __init__(self, value): self.value = value
    def __repr__(self): return f"Sym({self.value!r})"

class Op:
    __slots__ = ('value',)
    def __init__(self, value): self.value = value
    def __repr__(self): return f"Op({self.value!r})"

# Precedencia de operadores
PRECEDENCE = {
    '#': 1,
    '|': 2,
    '·': 3,
    '*': 4,
    '+': 4,
    '?': 4,
}
UNARY_POSTFIX = {'*', '+', '?'}
BINARY_OPS    = {'|', '·', '#'}


class RegexParser:
    def __init__(self, regex: str):
        self.regex = regex

    def to_postfix(self) -> list:
        tokens  = self._tokenize(self.regex)
        tokens  = self._insert_concatenation(tokens)
        postfix = self._shunting_yard(tokens)
        result = []
        for t in postfix:
            if isinstance(t, Sym):
                result.append(('SYM', t.value))
            else:
                result.append(('OP',  t.value))
        return result


    # Paso 1 — Tokenización
    def _tokenize(self, regex: str) -> list:
        tokens = []
        i = 0
        while i < len(regex):
            c = regex[i]

            # Entre comillas simples: 'a' o '\n'
            if c == "'":
                j = i + 1
                if j < len(regex) and regex[j] == '\\':
                    char = self._unescape(regex[j + 1])
                    tokens.append(Sym(char))
                    i = j + 3
                elif j < len(regex):
                    tokens.append(Sym(regex[j]))
                    i = j + 2
                else:
                    i += 1
                continue

            # Entre comillas dobles: "abc" o "a\nb"
            if c == '"':
                j = i + 1
                while j < len(regex) and regex[j] != '"':
                    if regex[j] == '\\':
                        tokens.append(Sym(self._unescape(regex[j + 1])))
                        j += 2
                    else:
                        tokens.append(Sym(regex[j]))
                        j += 1
                i = j + 1
                continue

            # Clases de caracteres: [a-z] o [^0-9]
            if c == '[':
                j = i + 1
                while j < len(regex) and regex[j] != ']':
                    j += 1
                tokens.append(Sym(regex[i:j + 1]))
                i = j + 1
                continue

            # Operadores y paréntesis
            if c in '()|*+?#':
                tokens.append(Op(c))
                i += 1
                continue

            # Ignorar espacios en blanco
            if c in ' \t\n\r':
                i += 1
                continue

            # Token especial 'eof' para marcar el final de la entrada
            if regex[i:i + 3] == 'eof':
                tokens.append(Sym('eof'))
                i += 3
                continue

            # Marcadores especiales para tokens
            if ord(c) >= 0xE000:
                tokens.append(Sym(c))
                i += 1
                continue

            # Carácter simple
            tokens.append(Sym(c))
            i += 1

        return tokens

    def _unescape(self, c: str) -> str:
        return {'n': '\n', 't': '\t', 'r': '\r',
                '\\': '\\', "'": "'", '"': '"'}.get(c, c)

    # Paso 2 — Inserción de concatenación explícita
    def _insert_concatenation(self, tokens: list) -> list:
        result = []
        for i, tok in enumerate(tokens):
            result.append(tok)
            if i + 1 < len(tokens):
                if self._needs_concat(tok, tokens[i + 1]):
                    result.append(Op('·'))
        return result

    def _needs_concat(self, left, right) -> bool:
        left_ok = isinstance(left, Sym) or (
            isinstance(left, Op) and left.value in (')', '*', '+', '?')
        )
        right_ok = isinstance(right, Sym) or (
            isinstance(right, Op) and right.value == '('
        )
        return left_ok and right_ok

    # Paso 3 — Shunting Yard para convertir a notación postfija
    def _shunting_yard(self, tokens: list) -> list:
        output   = []
        op_stack = []

        for tok in tokens:
            if isinstance(tok, Sym):
                output.append(tok)
                continue

            # Si es un operador, manejamos la precedencia y la pila de operadores
            v = tok.value
            if v == '(':
                op_stack.append(tok)

            elif v == ')':
                while op_stack and op_stack[-1].value != '(':
                    output.append(op_stack.pop())
                if op_stack:
                    op_stack.pop()  # discard '('

            elif v in UNARY_POSTFIX:
                output.append(tok)

            else:  # binary: | · #
                while (op_stack and
                       op_stack[-1].value != '(' and
                       op_stack[-1].value in PRECEDENCE and
                       PRECEDENCE[op_stack[-1].value] >= PRECEDENCE[v]):
                    output.append(op_stack.pop())
                op_stack.append(tok)

        while op_stack:
            output.append(op_stack.pop())

        return output


if __name__ == "__main__":
    cases = [
        ("'a'|'b'",       "alternation"),
        ("'a''b'",        "concat"),
        ("['a'-'z']+",    "class+"),
        ("'+'|'-'|'*'",   "operator literals"),
        ("('a'|'b')*'c'", "group*concat"),
    ]
    for regex, desc in cases:
        p = RegexParser(regex)
        print(f"{desc:25s} → {p.to_postfix()}")
