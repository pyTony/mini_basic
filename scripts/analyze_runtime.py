import ast
import sys
from collections import defaultdict

file_path = "runtime.py"

with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

tree = ast.parse(code)

print(f"File: {file_path}")
print(f"Total lines: {len(code.splitlines())}\n")

classes = []
functions = []
methods = defaultdict(list)

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        classes.append(node.name)
    elif isinstance(node, ast.FunctionDef):
        if any(isinstance(parent, ast.ClassDef) for parent in ast.walk(node)):
            # It's a method
            class_name = "Unknown"
            for parent in ast.walk(node):
                if isinstance(parent, ast.ClassDef):
                    class_name = parent.name
                    break
            methods[class_name].append(node.name)
        else:
            functions.append(node.name)

print("=== Top Level Classes ===")
for c in classes:
    print(f"- {c}")

print("\n=== Top Level Functions ===")
for f in functions:
    print(f"- {f}")

print(f"\n=== Methods in BASICInterpreter ({len(methods.get('BASICInterpreter', []))} methods) ===")
for m in sorted(methods.get('BASICInterpreter', [])):
    print(f"- {m}")

# Optional: save full tree
with open("runtime_ast_summary.txt", "w", encoding="utf-8") as f:
    f.write(ast.dump(tree, indent=2))
print("\nFull AST saved to runtime_ast_summary.txt")
