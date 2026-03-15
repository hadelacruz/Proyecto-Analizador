# Proyecto-Analizador

Generador de analizadores léxicos en Python a partir de una especificación `.yal`.

## Que hace

Este proyecto toma un archivo `.yal`, construye un AFD por método directo (árbol sintáctico + `followpos`), lo minimiza y genera un `lexer.py` listo para usar.

## Requisitos

- Python 3.10+
- Paquete Python `graphviz` (solo si usarás `--tree`)
- Graphviz instalado en el sistema (binario `dot` en `PATH`) para renderizar el árbol

## Instalación rápida (Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install graphviz
```

Opcional (si falla `--tree`): instala Graphviz Desktop y verifica:

```powershell
dot -V
```

## Cómo ejecutar

### 1) Generar lexer desde un `.yal`

```powershell
python main.py ejemplo.yal -o lexer.py
```

### 2) Generar lexer y dibujar árbol sintáctico

```powershell
python main.py ejemplo.yal -o lexer.py --tree
```

Salida esperada:
- `lexer.py` generado en la raíz del proyecto.
- Si usas `--tree`, imagen del árbol en `img/syntax_tree.png`.

### 3) Usar el lexer generado

```powershell
python lexer.py <archivo_entrada>
```

El lexer imprime:
- Tokens detectados
- Tabla de símbolos (para IDs)
- Errores léxicos con línea y columna

## Flujo interno

1. `SpecParser.py`: parsea macros (`let`) y reglas (`rule`) desde `.yal`.
2. `MacroExpander.py`: expande macros en cada regex de token.
3. `RegexUnifier.py`: unifica todas las regex en una sola con marcador `#`.
4. `RegexParser.py`: convierte regex unificada a notación postfix.
5. `SyntaxTreeBuilder.py`: construye árbol y calcula `nullable`, `firstpos`, `lastpos`, `followpos`.
6. `DirectDFAConstructor.py`: construye y minimiza el AFD.
7. `CodeGenerator.py`: genera `lexer.py`.
8. `TreeVisualizer.py` (opcional): renderiza el árbol con Graphviz.