from SyntaxTreeBuilder import SyntaxTreeBuilder, Node

class DFAState:
    _id_counter = 0

    def __init__(self, positions: frozenset[int]):
        DFAState._id_counter += 1
        self.id = DFAState._id_counter
        self.positions   = positions          # conjunto de posiciones de hojas
        self.transitions: dict[str, 'DFAState'] = {}
        self.is_accepting = False
        self.token_name:  str | None = None   # nombre del token
        self.token_priority: int = 999        # menor = mayor prioridad

    def __repr__(self):
        acc = f" → {self.token_name}" if self.is_accepting else ""
        return f"S{self.id}{acc}"


class DirectDFAConstructor:
    def __init__(self,
                 root: Node,
                 followpos: dict[int, set[int]],
                 position_map: dict[int, Node],
                 marker_to_token):
        
        self.root          = root
        self.followpos     = followpos
        self.position_map  = position_map
        self.marker_to_token = marker_to_token

        self.states:       list[DFAState] = []
        self.start_state:  DFAState | None = None

    def build(self) -> DFAState:
        DFAState._id_counter = 0

        start_positions = frozenset(self.root.firstpos)
        start = DFAState(start_positions)
        self._mark_accepting(start)
        self.start_state = start
        self.states = [start]

        worklist = [start]
        seen = {start_positions: start}

        while worklist:
            current = worklist.pop()

            # Recopilar todos los símbolos que aparecen en current.positions
            symbol_map: dict[str, set[int]] = {}
            for pos in current.positions:
                leaf = self.position_map[pos]
                syms = leaf.symbol if isinstance(leaf.symbol, set) else {leaf.symbol}
                for sym in syms:
                    symbol_map.setdefault(sym, set()).add(pos)

            for sym, positions_with_sym in symbol_map.items():
                # Nuevo estado = unión de followpos de todas las posiciones que leen sym
                next_positions = frozenset(
                    p for pos in positions_with_sym
                    for p in self.followpos.get(pos, set())
                )
                if not next_positions:
                    continue

                if next_positions not in seen:
                    new_state = DFAState(next_positions)
                    self._mark_accepting(new_state)
                    seen[next_positions] = new_state
                    self.states.append(new_state)
                    worklist.append(new_state)

                current.transitions[sym] = seen[next_positions]

        return self.start_state

    def minimize(self):
        # estados en grupos aceptantes
        groups: dict = {}
        non_accepting = []

        for state in self.states:
            if state.is_accepting:
                key = state.token_name
                groups.setdefault(key, []).append(state)
            else:
                non_accepting.append(state)

        partitions = list(groups.values())
        if non_accepting:
            partitions.append(non_accepting)

        changed = True
        while changed:
            changed = False
            new_partitions = []
            for group in partitions:
                split = self._split_group(group, partitions)
                if len(split) > 1:
                    changed = True
                new_partitions.extend(split)
            partitions = new_partitions

        # Construir nuevo DFA minimizado
        self._rebuild_from_partitions(partitions)
        return self.start_state

    def _mark_accepting(self, state: DFAState):
        for pos in state.positions:
            leaf = self.position_map[pos]
            sym  = leaf.symbol
            if isinstance(sym, str) and sym in self.marker_to_token:
                token = self.marker_to_token[sym]
                if token.priority < state.token_priority:
                    state.is_accepting   = True
                    state.token_name     = token.name
                    state.token_priority = token.priority


    def _split_group(self, group: list[DFAState],
                     partitions: list) -> list[list[DFAState]]:
        if len(group) <= 1:
            return [group]

        # Construir una búsqueda de índice de partición
        state_to_partition: dict[int, int] = {}
        for idx, part in enumerate(partitions):
            for s in part:
                state_to_partition[s.id] = idx

        def signature(state: DFAState):
            sig = {}
            for sym, target in state.transitions.items():
                sig[sym] = state_to_partition.get(target.id, -1)
            return tuple(sorted(sig.items()))

        buckets: dict = {}
        for state in group:
            key = signature(state)
            buckets.setdefault(key, []).append(state)

        return list(buckets.values())

    def _rebuild_from_partitions(self, partitions: list):
        # Primer estado en cada partición
        rep_map: dict[int, DFAState] = {}
        new_states = []

        for part in partitions:
            rep = part[0]
            new_states.append(rep)
            for state in part:
                rep_map[state.id] = rep

        # Reconectar transiciones
        for state in new_states:
            state.transitions = {
                sym: rep_map[target.id]
                for sym, target in state.transitions.items()
            }

        # Actualizar estado inicial
        self.start_state = rep_map[self.start_state.id]
        self.states = new_states


if __name__ == "__main__":
    from SpecParser import SpecParser, TokenSpec
    from MacroExpander import MacroExpander
    from RegexUnifier import RegexUnifier
    from RegexParser import RegexParser

    tokens = [
        TokenSpec("ID",     "(['a'-'z']['A'-'Z'])((['a'-'z']['A'-'Z'])|['0'-'9'])*", 1),
        TokenSpec("NUMBER", "['0'-'9']+", 2),
        TokenSpec("PLUS",   "'+'", 3),
    ]
    macros = {}

    unifier = RegexUnifier(tokens)
    unified, marker_map = unifier.unify()

    parser  = RegexParser(unified)
    postfix = parser.to_postfix()

    builder  = SyntaxTreeBuilder(postfix)
    root     = builder.build()

    constructor = DirectDFAConstructor(
        root, builder.followpos, builder.position_map, marker_map
    )
    start = constructor.build()
    constructor.minimize()

    print(f"States: {len(constructor.states)}")
    print(f"Start:  {constructor.start_state}")
    for state in constructor.states:
        if state.is_accepting:
            print(f"  {state} accepts {state.token_name}")
        for sym, target in sorted(state.transitions.items()):
            if ord(sym) < 128:
                print(f"  {state} --{sym!r}--> {target}")
