"""Builds one submission ipynb: replaces `from src.x import ...` with the code of src/ modules.

Usage (from the repo root):
    uv run --project lab-N python .claude/skills/pack-submission/pack.py lab-N/lab-N.ipynb

Conventions the script relies on:
- notebook and src import only as `from src.<module> import name[, name as alias]`;
- lines with `# dev-only` and `# user-owned` marker lines are removed;
- `if __name__ == "__main__":` blocks in modules are removed (in a notebook __name__ == "__main__").
"""

import argparse
import ast
import re
import sys
from pathlib import Path

import nbformat

DEV_ONLY = "# dev-only"
USER_OWNED = "# user-owned"
SRC_MENTION = re.compile(r"\bsrc\.")


class PackError(Exception):
    pass


def parse_code(source: str, where: str) -> ast.Module | None:
    # ast cannot parse IPython magics and shell commands: blank them, keeping line numbers
    lines = [
        "" if line.lstrip().startswith(("%", "!")) else line
        for line in source.splitlines()
    ]
    try:
        return ast.parse("\n".join(lines))
    except SyntaxError as e:
        if SRC_MENTION.search(source):
            raise PackError(f"{where}: cannot parse code ({e.msg}, line {e.lineno})") from e
        return None


def src_imports(tree: ast.Module, where: str) -> list[ast.ImportFrom]:
    found = []
    for node in tree.body:
        if isinstance(node, ast.Import) and any(a.name.split(".")[0] == "src" for a in node.names):
            raise PackError(f"{where}:{node.lineno}: use `from src.<module> import name`")
        if isinstance(node, ast.ImportFrom):
            if node.level > 0 or node.module == "src":
                raise PackError(f"{where}:{node.lineno}: use `from src.<module> import name`")
            if node.module and node.module.startswith("src."):
                found.append(node)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("src.") and node not in found:
            raise PackError(f"{where}:{node.lineno}: src imports must be at top level")
    return found


def is_main_guard(node: ast.stmt) -> bool:
    if not isinstance(node, ast.If) or not isinstance(node.test, ast.Compare):
        return False
    t = node.test
    return (
        isinstance(t.left, ast.Name)
        and t.left.id == "__name__"
        and len(t.comparators) == 1
        and isinstance(t.comparators[0], ast.Constant)
        and t.comparators[0].value == "__main__"
    )


def rewrite(source: str, tree: ast.Module, imports: list[ast.ImportFrom], drop: list[ast.stmt] = ()) -> str:
    """Removes src imports (keeping assignments for aliases) and the `drop` blocks."""
    lines = source.splitlines()
    replacements: dict[int, list[str]] = {}
    removed: set[int] = set()
    for node in [*imports, *drop]:
        span = range(node.lineno - 1, node.end_lineno)
        removed.update(span)
        if isinstance(node, ast.ImportFrom):
            indent = re.match(r"\s*", lines[node.lineno - 1]).group()
            replacements[node.lineno - 1] = [
                f"{indent}{a.asname} = {a.name}" for a in node.names if a.asname and a.asname != a.name
            ]
    out = []
    for i, line in enumerate(lines):
        if i in replacements:
            out.extend(replacements[i])
        if i not in removed:
            out.append(line)
    return re.sub(r"\n{4,}", "\n\n\n", "\n".join(out)).strip("\n")


def strip_dev_only(source: str) -> str:
    """Removes `# dev-only` lines and `# user-owned` marker lines."""
    return "\n".join(
        line
        for line in source.splitlines()
        if DEV_ONLY not in line and line.strip() != USER_OWNED
    )


class Inliner:
    def __init__(self, src_dir: Path):
        self.src_dir = src_dir
        self.done: set[str] = set()
        self._visiting: set[str] = set()

    def module_cells(self, module: str) -> list[str]:
        """Code of a module and its src dependencies (dependencies first), each module once."""
        if module in self.done:
            return []
        if module in self._visiting:
            raise PackError(f"circular import in src: {module}")
        path = self.src_dir / f"{module.replace('.', '/')}.py"
        if not path.exists():
            raise PackError(f"file not found: {path}")
        self._visiting.add(module)
        where = f"src/{path.relative_to(self.src_dir)}"
        source = strip_dev_only(path.read_text())
        tree = parse_code(source, where)
        imports = src_imports(tree, where)
        cells = []
        for node in imports:
            cells += self.module_cells(node.module.removeprefix("src."))
        guards = [n for n in tree.body if is_main_guard(n)]
        body = rewrite(source, tree, imports, guards)
        cells.append(f"# ---- {where} ----\n{body}")
        self._visiting.discard(module)
        self.done.add(module)
        return cells


def pack(nb_path: Path, out_path: Path, clear_outputs: bool) -> list[str]:
    nb = nbformat.read(nb_path, as_version=4)
    inliner = Inliner(nb_path.parent / "src")
    new_cells = []
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != "code":
            new_cells.append(cell)
            continue
        source = strip_dev_only(cell.source)
        tree = parse_code(source, f"cell {idx}")
        imports = src_imports(tree, f"cell {idx}") if tree else []
        for node in imports:
            for code in inliner.module_cells(node.module.removeprefix("src.")):
                new_cells.append(nbformat.v4.new_code_cell(code))
        if imports:
            source = rewrite(source, tree, imports)
        if not source.strip():
            continue
        cell.source = source
        if clear_outputs:
            cell.outputs, cell.execution_count = [], None
        new_cells.append(cell)
    nb.cells = new_cells

    warnings = [
        f"cell {i}: `src.` is still referenced"
        for i, c in enumerate(nb.cells)
        if c.cell_type == "code" and SRC_MENTION.search(c.source) and not c.source.startswith("# ---- src/")
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(nb, out_path)
    return warnings


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="default: <lab>/submission/<name>.ipynb")
    parser.add_argument("--clear-outputs", action="store_true", help="clear outputs (kept by default)")
    args = parser.parse_args()

    out = args.output or args.notebook.parent / "submission" / args.notebook.name
    try:
        warnings = pack(args.notebook, out, args.clear_outputs)
    except PackError as e:
        sys.exit(f"Error: {e}")
    for w in warnings:
        print(f"Warning: {w}")
    print(f"Done: {out}")


if __name__ == "__main__":
    main()
