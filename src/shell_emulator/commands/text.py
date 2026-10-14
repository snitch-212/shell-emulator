"""Команды обработки текста: uniq."""

import itertools

from ..errors import ShellError
from ..vfs import READ, check_access
from .options import split_options

MAX_UNIQ_OPERANDS = 1
SINGLE = 1


def cmd_uniq(shell, args):
    """Убрать повторяющиеся соседние строки файла VFS.

    uniq [-c] [-d] [-u] [-i] файл

    * -c — выводить перед строкой число повторов;
    * -d — выводить только повторяющиеся строки;
    * -u — выводить только неповторяющиеся строки;
    * -i — сравнивать строки без учёта регистра.
    """
    flags, operands = split_options(args, "cdui")
    if not operands:
        raise ShellError("missing operand: file")
    if len(operands) > MAX_UNIQ_OPERANDS:
        raise ShellError(f"extra operand '{operands[1]}'")
    for line, count in group_lines(_read_lines(shell, operands[0]),
                                   "i" in flags):
        if _selected(count, flags):
            shell.write(f"{count:>7} {line}" if "c" in flags else line)


def group_lines(lines, ignore_case=False):
    """Сгруппировать соседние одинаковые строки.

    :return: список пар (первая строка группы, число повторов)
    """
    key = str.lower if ignore_case else None
    return [(group[0], len(group))
            for group in (list(items) for _, items in
                          itertools.groupby(lines, key=key))]


def _read_lines(shell, path):
    """Прочитать строки текстового файла VFS."""
    node = shell.vfs.resolve(path)
    if node.is_dir:
        raise ShellError(f"{path}: Is a directory")
    check_access(node, READ, path)
    return node.to_bytes().decode("utf-8", errors="replace").splitlines()


def _selected(count, flags):
    """Проверить, выводится ли группа с учётом опций -d и -u."""
    if "d" in flags and count == SINGLE:
        return False
    return not ("u" in flags and count > SINGLE)
