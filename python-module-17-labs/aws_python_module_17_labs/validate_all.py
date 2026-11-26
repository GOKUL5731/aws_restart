"""Compile all Python files in this practice pack."""
from pathlib import Path
import compileall
root = Path(__file__).parent
ok = compileall.compile_dir(root, quiet=1)
print("Syntax check:", "PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
