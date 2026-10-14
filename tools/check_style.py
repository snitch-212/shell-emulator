"""Проверка репозитория по перечню нарушений из сборника заданий.

Запуск: python tools/check_style.py [каталог ...]
Проверяются: длина строк (P2) и файлов (P1), длина функций (Ф1),
число аргументов (A1), docstring (K1), цикломатическая сложность (Ц1),
магические числа в сравнениях (M1) и имена по PEP8 (И1).
"""

import ast
import re
import sys
from pathlib import Path

MAX_LINE = 80
MAX_FILE_LINES = 1000
MAX_FUNCTION_LINES = 40
MAX_ARGS = 7
MAX_COMPLEXITY = 10
ALLOWED_NUMBERS = (0,)
SNAKE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$")
CAMEL = re.compile(r"^_?[A-Z][A-Za-z0-9]*$")
UPPER = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
BRANCHES = (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler,
            ast.Assert, ast.comprehension, ast.match_case)
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)


def complexity(func):
    """Посчитать цикломатическую сложность функции (по МакКейбу)."""
    score = 1
    for node in ast.walk(func):
        if isinstance(node, BRANCHES):
            score += 1
        elif isinstance(node, ast.BoolOp):
            score += len(node.values) - 1
    return score


def check_function(node, report):
    """Проверить размер, аргументы, сложность и имя функции."""
    size = node.end_lineno - node.lineno + 1
    if size > MAX_FUNCTION_LINES:
        report(node, f"Ф1 функция {node.name}: {size} строк")
    args = node.args
    count = len(args.posonlyargs + args.args + args.kwonlyargs)
    if count > MAX_ARGS:
        report(node, f"A1 функция {node.name}: {count} аргументов")
    score = complexity(node)
    if score > MAX_COMPLEXITY:
        report(node, f"Ц1 функция {node.name}: сложность {score}")
    if not SNAKE.match(node.name):
        report(node, f"И1 имя функции {node.name}")


def check_names(node, report):
    """Проверить имена переменных на соответствие PEP8."""
    for target in ast.walk(node):
        if isinstance(target, ast.Name) and \
                isinstance(target.ctx, ast.Store):
            name = target.id
            if name != "_" and \
                    not (SNAKE.match(name) or UPPER.match(name)):
                report(target, f"И1 имя переменной {name}")


def check_compare(node, report):
    """Найти числовые литералы в сравнениях (магические числа)."""
    for operand in [node.left, *node.comparators]:
        if isinstance(operand, ast.UnaryOp):
            operand = operand.operand
        if isinstance(operand, ast.Constant) and \
                type(operand.value) in (int, float) and \
                operand.value not in ALLOWED_NUMBERS:
            report(node, f"M1 магическое число {operand.value}")


def check_tree(tree, report):
    """Обойти синтаксическое дерево и проверить все узлы."""
    if ast.get_docstring(tree) is None:
        report(tree, "K1 нет docstring модуля")
    for node in ast.walk(tree):
        if isinstance(node, (*FUNCTIONS, ast.ClassDef)) and \
                ast.get_docstring(node) is None:
            report(node, f"K1 нет docstring у {node.name}")
        if isinstance(node, FUNCTIONS):
            check_function(node, report)
        elif isinstance(node, ast.ClassDef) and \
                not CAMEL.match(node.name):
            report(node, f"И1 имя класса {node.name}")
        elif isinstance(node, ast.Compare):
            check_compare(node, report)
    check_names(tree, report)


def check_file(path):
    """Проверить один файл и вернуть список найденных нарушений."""
    problems = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    def report(node, message):
        """Запомнить нарушение с номером строки узла."""
        problems.append(f"{path}:{getattr(node, 'lineno', 1)}: {message}")

    if len(lines) > MAX_FILE_LINES:
        report(None, f"P1 файл слишком большой: {len(lines)} строк")
    for number, line in enumerate(lines, start=1):
        if len(line) > MAX_LINE:
            problems.append(f"{path}:{number}: P2 строка {len(line)} "
                            "символов")
    check_tree(ast.parse(text, filename=str(path)), report)
    return problems


def main(paths):
    """Проверить все .py-файлы в указанных каталогах."""
    roots = [Path(p) for p in paths or ["src", "tests", "tools"]]
    problems = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            problems.extend(check_file(path))
    for problem in problems:
        print(problem)
    print(f"Нарушений найдено: {len(problems)}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
