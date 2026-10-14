"""Команда chmod: изменение прав доступа к узлам VFS (только в памяти).

Формат: chmod [-R] [-v] РЕЖИМ путь ...

РЕЖИМ задаётся восьмеричным числом (755, 0644) или символьно:
список через запятую из выражений ``[ugoa]*([-+=][rwx]*)+``,
например ``u+x``, ``go-w``, ``a=r``, ``u=rwx,g=rx,o=``, ``+x``.
"""

import re
import stat

from ..errors import ShellError
from ..vfs import PERMISSION_MASK

OCTAL = re.compile(r"[0-7]{1,4}")
CLAUSE = re.compile(r"([ugoa]*)((?:[-+=][rwx]*)+)")
OPERATION = re.compile(r"([-+=])([rwx]*)")
OPTION = re.compile(r"-[Rv]+")
WHO_BITS = {"u": 0o700, "g": 0o070, "o": 0o007, "a": 0o777}
PERM_BITS = {"r": 0o444, "w": 0o222, "x": 0o111}
MIN_OPERANDS = 2
STATUS_ERROR = 1


def cmd_chmod(shell, args):
    """Изменить права доступа файлов и каталогов VFS."""
    flags, operands = _split_args(args)
    if len(operands) < MIN_OPERANDS:
        raise ShellError("missing operand")
    spec, paths = operands[0], operands[1:]
    apply_mode(spec, 0)
    status = 0
    for path in paths:
        try:
            node = shell.vfs.resolve(path)
        except ShellError as exc:
            shell.error(f"chmod: cannot access '{path}': "
                        f"{str(exc).removeprefix(path + ': ')}")
            status = STATUS_ERROR
            continue
        targets = shell.vfs.walk(node) if "R" in flags else [node]
        for target in targets:
            _change(shell, target, spec, "v" in flags)
    return status


def _split_args(args):
    """Отделить опции -R и -v от режима (режим может начинаться с -)."""
    rest = list(args)
    flags = set()
    while rest and OPTION.fullmatch(rest[0]):
        flags.update(rest.pop(0)[1:])
    if rest and rest[0] == "--":
        rest.pop(0)
    return flags, rest


def apply_mode(spec, mode):
    """Вычислить новые права из режима ``spec`` и текущих ``mode``.

    :raises ShellError: если режим записан неверно
    """
    if OCTAL.fullmatch(spec):
        return int(spec, 8) & PERMISSION_MASK
    for clause in spec.split(","):
        mode = _apply_clause(clause, mode, spec)
    return mode


def _apply_clause(clause, mode, spec):
    """Применить одно символьное выражение, например ``go-w``."""
    match = CLAUSE.fullmatch(clause)
    if match is None:
        raise ShellError(f"invalid mode: '{spec}'")
    who = _mask(match.group(1) or "a", WHO_BITS)
    for operator, letters in OPERATION.findall(match.group(2)):
        bits = _mask(letters, PERM_BITS) & who
        if operator == "+":
            mode |= bits
        elif operator == "-":
            mode &= ~bits
        else:
            mode = (mode & ~who) | bits
    return mode & PERMISSION_MASK


def _mask(letters, table):
    """Объединить битовые маски для букв ``letters`` по таблице."""
    result = 0
    for letter in letters:
        result |= table[letter]
    return result


def _change(shell, node, spec, verbose):
    """Изменить права одного узла и при -v сообщить об этом."""
    old = node.mode
    node.mode = apply_mode(spec, old)
    if verbose:
        verb = "changed from" if old != node.mode else "retained as"
        new = "" if old == node.mode else f" to {_describe(node.mode)}"
        shell.write(f"mode of '{node.path()}' {verb} "
                    f"{_describe(old)}{new}")


def _describe(mode):
    """Описать права как 0755 (rwxr-xr-x)."""
    return f"{mode:04o} ({stat.filemode(mode)[1:]})"
