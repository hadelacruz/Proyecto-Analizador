from DirectDFAConstructor import DFAState
 
 
class CodeGenerator:
    def __init__(self,
                 states:       list[DFAState],
                 start_state:  DFAState,
                 header:       str = "",
                 trailer:      str = ""):
        self.states      = states
        self.start_state = start_state
        self.header      = header
        self.trailer     = trailer
 
    def generate(self, output_path: str = "lexer.py"):
        code = self._build_code()
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"Analizador léxico generado en {output_path}")
 
 
    def _build_code(self) -> str:
        lines = []
 
        lines += [
            "# Grupo 5 - Proyecto de Analizador Léxico",
            "# Diego Oswaldo Flores Rivas  - 23714",
            "# Daniel Oswaldo Juárez Herrera - 23709",
            "# Humberto Alexander de la Cruz  - 23735",
            "# lexer.py — Analizador léxico generado automáticamente",
            "# Uso:  python lexer.py <archivo_entrada>",
            "",
        ]
 
        if self.header:
            lines += ["# header del .yal", self.header, ""]
 
        lines.append("import sys")
        lines.append("")
 
        # Tabla de transiciones
        state_ids = {s.id: idx for idx, s in enumerate(self.states)}
        start_idx = state_ids[self.start_state.id]
 
        lines.append("# Tabla de transiciones: TRANSITIONS[estado][char] = estado_siguiente")
        lines.append(f"START_STATE = {start_idx}")
        lines.append("")
        lines.append("TRANSITIONS: dict[int, dict[str, int]] = {")
        for state in self.states:
            idx = state_ids[state.id]
            items = ", ".join(
                f"{sym!r}: {state_ids[tgt.id]}"
                for sym, tgt in sorted(state.transitions.items())
                if sym != '#'   # '#' es marcador interno, no transiciona
            )
            lines.append(f"    {idx}: {{{items}}},")
        lines.append("}")
        lines.append("")
 
        # Estados de aceptación
        lines.append("# Estados aceptantes: ACCEPTING[estado] = nombre_token")
        lines.append("ACCEPTING: dict[int, str] = {")
        for state in self.states:
            if state.is_accepting:
                lines.append(f"    {state_ids[state.id]}: {state.token_name!r},")
        lines.append("}")
        lines.append("")
 
        lines.append("# Nombres de tokens que usan tabla de símbolos (identificadores)")
        lines.append("ID_TOKENS: set[str] = {")
        id_tokens = {s.token_name for s in self.states
                     if s.is_accepting and s.token_name and 'ID' in s.token_name}
        for name in sorted(id_tokens):
            lines.append(f"    {name!r},")
        lines.append("}")
        lines.append("")
 
        # Clase Token
        lines += [
            "class Token:",
            "    def __init__(self, type_: str, value):",
            "        self.type  = type_",
            "        self.value = value",
            "",
            "    def __repr__(self):",
            "        return f'Token({self.type}, {self.value!r})'",
            "",
        ]
 
        # Tabla de símbolos
        lines += [
            "class SymbolTable:",
            "    def __init__(self):",
            "        self._table: dict[str, int] = {}",
            "        self._next_index = 0",
            "",
            "    def insert(self, lexeme: str) -> int:",
            "        if lexeme not in self._table:",
            "            self._table[lexeme] = self._next_index",
            "            self._next_index += 1",
            "        return self._table[lexeme]",
            "",
            "    def get_index(self, lexeme: str) -> int | None:",
            "        return self._table.get(lexeme)",
            "",
            "    def entries(self) -> list[tuple[str, int]]:",
            "        return sorted(self._table.items(), key=lambda x: x[1])",
            "",
            "    def __repr__(self):",
            "        rows = [f'  {idx}: {lex!r}' for lex, idx in self.entries()]",
            "        return 'SymbolTable(\\n' + '\\n'.join(rows) + '\\n)'",
            "",
        ]
 
        # Clase LexicalError
        lines += [
            "class LexicalError:",
            "    def __init__(self, char: str, line: int, column: int):",
            "        self.char   = char",
            "        self.line   = line",
            "        self.column = column",
            "",
            "    def __repr__(self):",
            "        return (f'Error léxico: carácter {self.char!r} no reconocido '",
            "                f'en línea {self.line}, columna {self.column}')",
            "",
        ]
 
        # Función tokenize
        lines += [
            "def tokenize(source: str) -> tuple[list[Token], SymbolTable, list[LexicalError]]:",
            "    tokens       = []",
            "    symbol_table = SymbolTable()",
            "    errors       = []",
            "    i            = 0",
            "    line         = 1",
            "    column       = 1",
            "    n            = len(source)",
            "",
            "    while i < n:",
            "        # Saltar espacios en blanco",
            "        if source[i] in (' ', '\\t', '\\r'):",
            "            column += 1",
            "            i += 1",
            "            continue",
            "        if source[i] == '\\n':",
            "            line  += 1",
            "            column = 1",
            "            i     += 1",
            "            continue",
            "",
            "        # Longest-match con el AFD",
            "        state       = START_STATE",
            "        last_accept = None   # (token_name, end_pos)",
            "        j           = i",
            "",
            "        while j < n:",
            "            c     = source[j]",
            "            trans = TRANSITIONS.get(state, {})",
            "            if c not in trans:",
            "                break",
            "            state = trans[c]",
            "            j    += 1",
            "            if state in ACCEPTING:",
            "                last_accept = (ACCEPTING[state], j)",
            "",
            "        if last_accept is None:",
            "            errors.append(LexicalError(source[i], line, column))",
            "            i      += 1",
            "            column += 1",
            "        else:",
            "            token_name, end_pos = last_accept",
            "            lexeme = source[i:end_pos]",
            "",
            "            # Construir el token con 2 atributos",
            "            if token_name in ID_TOKENS:",
            "                # value = índice en tabla de símbolos",
            "                idx   = symbol_table.insert(lexeme)",
            "                token = Token(token_name, idx)",
            "            else:",
            "                # value = lexema literal",
            "                token = Token(token_name, lexeme)",
            "",
            "            tokens.append(token)",
            "            column += (end_pos - i)",
            "            line   += lexeme.count('\\n')",
            "            i       = end_pos",
            "",
            "    return tokens, symbol_table, errors",
            "",
        ]
 
        # Main
        lines += [
            "def main():",
            "    if len(sys.argv) < 2:",
            "        print('Uso: python lexer.py <archivo_entrada>')",
            "        sys.exit(1)",
            "",
            "    with open(sys.argv[1], 'r', encoding='utf-8') as f:",
            "        source = f.read()",
            "",
            "    tokens, symbol_table, errors = tokenize(source)",
            "",
            "    print('=== TOKENS ===')",
            "    for tok in tokens:",
            "        print(tok)",
            "",
            "    if symbol_table.entries():",
            "        print('\\n=== TABLA DE SÍMBOLOS ===')",
            "        print(symbol_table)",
            "",
            "    if errors:",
            "        print('\\n=== ERRORES LÉXICOS ===')",
            "        for err in errors:",
            "            print(err)",
            "",
        ]
 
        if self.trailer:
            lines += ["# trailer del .yal ", self.trailer, ""]
 
        lines += ["", "if __name__ == '__main__':", "    main()"]
 
        return "\n".join(lines)