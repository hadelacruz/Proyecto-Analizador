def expand_char_class(class_token: str) -> set:

    inner = class_token[1:-1].strip()   # eliminar [ y ]
    negated = inner.startswith('^')
    if negated:
        inner = inner[1:].strip()
 
    tokens = _tokenize_class_inner(inner)
    chars = set()
    j = 0
    while j < len(tokens):
        if j + 2 < len(tokens) and tokens[j + 1] == '-':
            start = tokens[j]
            end   = tokens[j + 2]
            for code in range(ord(start), ord(end) + 1):
                chars.add(chr(code))
            j += 3
        else:
            chars.add(tokens[j])
            j += 1
 
    if negated:
        all_printable = set(chr(i) for i in range(32, 127))
        chars = all_printable - chars
 
    return chars
 
 
def _tokenize_class_inner(inner: str) -> list:
    tokens = []
    i = 0
    while i < len(inner):
        c = inner[i]
        if c == "'":
            # Secuencia de escape: '\n' o carácter simple: 'a'
            if i + 1 < len(inner) and inner[i + 1] == '\\':
                escape_map = {'n': '\n', 't': '\t', 'r': '\r', '\\': '\\', "'": "'"}
                ch = escape_map.get(inner[i + 2], inner[i + 2])
                tokens.append(ch)
                i += 4
            else:
                tokens.append(inner[i + 1])
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


    # Paso 1 — Tokenizacion 
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
 
            # Entre comillas dobles: "abc"
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
 
            # Clases de caracteres: ['a'-'z'] o [^'0'-'9']
            if c == '[':
                j = i + 1
                while j < len(regex) and regex[j] != ']':
                    j += 1
                char_set = expand_char_class(regex[i:j + 1])
                tokens.append(Sym(char_set))
                i = j + 1
                continue
 
            # Operadores y paréntesis -> siempre Op
            if c in '()|*+?':
                tokens.append(Op(c))
                i += 1
                continue
 
            # Ignorar espacios en blanco
            if c in ' \t\n\r':
                i += 1
                continue
 
            # Marcadores Unicode privados (de RegexUnifier)
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
                    op_stack.pop()  # descartar '('

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
    from SpecParser import SpecParser
    from MacroExpander import MacroExpander
    from RegexUnifier import RegexUnifier
    import sys
    parser = SpecParser(sys.argv[1])
    tokens, macros = parser.parse()

    expander = MacroExpander(tokens, macros)
    expanded = expander.expand()

    unifier = RegexUnifier(expanded)
    unified, tokensUnified = unifier.unify()

    p = RegexParser(unified)
    print(f"{p.to_postfix()}")
