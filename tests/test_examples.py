from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def test_examples_resolve_package_when_run_as_scripts():
    for example in sorted((ROOT / "examples").glob("*.py")):
        source = example.read_text()
        smoke_test = f"""
import ast
source = {source!r}
tree = ast.parse(source)
prefix = []
for node in tree.body:
    if isinstance(node, ast.ImportFrom) and (node.module or '').startswith('mastering_rag'):
        break
    prefix.append(node)
prefix.append(ast.Import(names=[ast.alias(name='mastering_rag')]))
module = ast.fix_missing_locations(ast.Module(body=prefix, type_ignores=[]))
exec(compile(module, {str(example)!r}, 'exec'), {{'__file__': {str(example)!r}}})
"""
        result = subprocess.run(
            [sys.executable, "-I", "-S", "-c", smoke_test],
            cwd=example.parent,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"{example.name}: {result.stderr}"
