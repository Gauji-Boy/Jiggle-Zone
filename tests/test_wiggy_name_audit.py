"""Fail the build if a hardcoded Wiggy group name comes back.

    python tests/test_wiggy_name_audit.py
    python tests/test_wiggy_name_audit.py --selftest

3.1 replaced 36 scattered `node_group.name == "Wiggy 0.1"` checks with one allow-list so
that `Wiggy 0.2.0` works everywhere. Every one of those sites failed *silently* when it
missed — a panel just drew itself empty — so a later feature can reintroduce the same bug
without any visible error. This audit pins the compatibility definition and the asset map
as the only places allowed to name a Wiggy group.
"""

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = os.path.join(ROOT, "jiggle_zone")

LITERALS = ("Wiggy 0.1", "Wiggy_0.1", "Wiggy 0.2.0", "Wiggy_0.2.0")

# The only assignments permitted to name a group.
ALLOWED_NAMES = ("WIGGY_GROUPS", "WIGGY_NEW_GROUP", "ASSET_GROUP_FILES")

COMPARISON_OPERATORS = (ast.Eq, ast.NotEq, ast.In, ast.NotIn)


def allowed_lines(tree):
    """Line numbers covered by the compatibility definition and the asset map."""
    spans = set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ALLOWED_NAMES:
                found.add(target.id)
                spans.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
    return spans, found


def comparison_violations(tree):
    """Any comparison whose literal side names a Wiggy group."""
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not any(isinstance(op, COMPARISON_OPERATORS) for op in node.ops):
            continue
        operands = [node.left] + list(node.comparators)
        if any(isinstance(o, ast.Constant) and isinstance(o.value, str) and o.value in LITERALS
               for o in operands):
            offenders.append(node.lineno)
        for operand in operands:
            if isinstance(operand, (ast.Set, ast.List, ast.Tuple)):
                if any(isinstance(e, ast.Constant) and e.value in LITERALS for e in operand.elts):
                    offenders.append(node.lineno)
    return sorted(set(offenders))


def audit(text, filename="<memory>"):
    tree = ast.parse(text)
    spans, found = allowed_lines(tree)

    problems = []
    missing = [name for name in ALLOWED_NAMES if name not in found]
    if missing:
        problems.append(f"{filename}: compatibility definition missing: {', '.join(missing)}")

    for number, line in enumerate(text.split("\n"), 1):
        if not any(literal in line for literal in LITERALS):
            continue
        if number in spans:
            continue
        problems.append(f"{filename}:{number}: hardcoded Wiggy name outside the allow-list: {line.strip()}")

    for number in comparison_violations(tree):
        problems.append(f"{filename}:{number}: comparison against a hardcoded Wiggy name")

    return problems


def selftest():
    """Prove the audit fires on a regression, and stays quiet on the real source."""
    injected = (
        'WIGGY_GROUPS = ("Wiggy 0.1", "Wiggy 0.2.0")\n'
        'WIGGY_NEW_GROUP = "Wiggy 0.2.0"\n'
        'ASSET_GROUP_FILES = {"Wiggy 0.1": "Wiggy_0.1.blend"}\n'
        "def f(mod):\n"
        '    return mod.node_group.name == "Wiggy 0.1"\n'
    )
    problems = audit(injected, "<injected>")
    if len(problems) < 1:
        return [f"selftest failed: injected regression not detected ({problems})"], 1
    if not any("hardcoded Wiggy name" in p or "hardcoded" in p for p in problems):
        return [f"selftest failed: unexpected problems only: {problems}"], 1
    print(f"PASS selftest: injected regression reported ({len(problems)} problem(s))")
    for problem in problems:
        print("     " + problem)
    return [], 0


def main():
    if "--selftest" in sys.argv:
        problems, code = selftest()
        for problem in problems:
            print("FAIL " + problem)
        return code

    failures = []
    sources = []
    for base, _dirs, files in os.walk(PACKAGE):
        for name in sorted(files):
            if name.endswith(".py"):
                sources.append(os.path.join(base, name))

    print(f"auditing {len(sources)} file(s) under jiggle_zone/")
    for path in sources:
        text = open(path, encoding="utf-8").read()
        problems = audit(text, os.path.relpath(path, ROOT))
        failures.extend(problems)

    for problem in failures:
        print("FAIL " + problem)
    print("RESULT", "PASS" if not failures else f"FAIL ({len(failures)} problem(s))")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
