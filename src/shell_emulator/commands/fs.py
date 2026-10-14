"""Команды навигации по VFS: ls, cd, pwd."""

import stat
import time

from ..errors import ShellError
from ..vfs import EXECUTE, READ, check_access
from .options import split_options

MAX_CD_ARGS = 1
SINGLE_OPERAND = 1
DIR_SIZE = 4096
RECENT_SECONDS = 180 * 24 * 3600
RECENT_FORMAT = "%b %d %H:%M"
OLD_FORMAT = "%b %d  %Y"
STATUS_ERROR = 1


def cmd_pwd(shell, args):
    """Вывести абсолютный путь текущего каталога: pwd [-L|-P]."""
    _, operands = split_options(args, "LP")
    if operands:
        raise ShellError("too many arguments")
    shell.write(shell.vfs.cwd.path())


def cmd_cd(shell, args):
    """Сменить текущий каталог: cd [путь | ~ | -]."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("too many arguments")
    vfs = shell.vfs
    target = args[0] if args else vfs.home
    if target == "-":
        if vfs.previous is None:
            raise ShellError("OLDPWD not set")
        target = vfs.previous
        shell.write(target)
    node = vfs.resolve(target)
    if not node.is_dir:
        raise ShellError(f"{target}: Not a directory")
    check_access(node, EXECUTE, target)
    vfs.previous = vfs.cwd.path()
    vfs.cwd = node


def cmd_ls(shell, args):
    """Вывести содержимое каталогов: ls [-l] [-a] [путь ...]."""
    flags, paths = split_options(args, "la")
    status = 0
    targets = paths or ["."]
    with_headers = len(targets) > SINGLE_OPERAND
    for index, path in enumerate(targets):
        try:
            node = shell.vfs.resolve(path)
            _list_node(shell, node, path, flags, with_headers)
        except ShellError as exc:
            shell.error(f"ls: cannot access '{path}': "
                        f"{str(exc).removeprefix(path + ': ')}")
            status = STATUS_ERROR
        if _needs_separator(index, targets):
            shell.write()
    return status


def _needs_separator(index, targets):
    """Нужна ли пустая строка между выводами нескольких каталогов."""
    return index < len(targets) - 1


def _list_node(shell, node, path, flags, with_header):
    """Вывести один операнд ls: файл или содержимое каталога."""
    if not node.is_dir:
        _print_entries(shell, [(path, node)], flags)
        return
    check_access(node, READ, path)
    if with_header:
        shell.write(f"{path}:")
    entries = sorted(node.children.items())
    if "a" in flags:
        entries = [(".", node), ("..", node.parent or node)] + entries
    else:
        entries = [item for item in entries if not item[0].startswith(".")]
    _print_entries(shell, entries, flags)


def _print_entries(shell, entries, flags):
    """Вывести список (имя, узел) в кратком или длинном формате."""
    if "l" not in flags:
        if entries:
            shell.write("  ".join(name for name, _ in entries))
        return
    sizes = [_size(node) for _, node in entries]
    width = len(str(max(sizes, default=0)))
    for (name, node), size in zip(entries, sizes):
        shell.write(_long_line(shell, name, node, size, width))


def _long_line(shell, name, node, size, width):
    """Сформировать строку формата ls -l."""
    kind = stat.S_IFDIR if node.is_dir else stat.S_IFREG
    links = len(node.children) + 2 if node.is_dir else 1
    return (f"{stat.filemode(kind | node.mode)} {links:>2} {shell.user} "
            f"{shell.user} {size:>{width}} {_format_time(node.mtime)} "
            f"{name}")


def _size(node):
    """Вернуть размер узла для ls -l."""
    return DIR_SIZE if node.is_dir else node.size()


def _format_time(mtime):
    """Отформатировать время изменения как ls: свежие — со временем."""
    recent = abs(time.time() - mtime) < RECENT_SECONDS
    return time.strftime(RECENT_FORMAT if recent else OLD_FORMAT,
                         time.localtime(mtime))
