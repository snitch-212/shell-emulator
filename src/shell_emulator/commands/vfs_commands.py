"""Служебные команды для работы с VFS: vfs-save и vfs-info."""

from ..errors import ShellError
from ..vfs import save_zip

SAVE_ARGS = 1
TREE_BRANCH = "├── "
TREE_LAST = "└── "
TREE_PIPE = "│   "
TREE_SPACE = "    "


def cmd_vfs_save(shell, args):
    """Сохранить текущее состояние VFS в ZIP-архив: vfs-save путь."""
    if not args:
        raise ShellError("missing operand: path to ZIP archive")
    if len(args) > SAVE_ARGS:
        raise ShellError("too many arguments")
    save_zip(shell.vfs, args[0])
    shell.write(f"VFS saved to {args[0]}")


def cmd_vfs_info(shell, args):
    """Показать источник VFS и дерево каталогов: vfs-info [путь]."""
    node = shell.vfs.resolve(args[0]) if args else shell.vfs.root
    source = shell.vfs.source or "(default VFS in memory)"
    nodes = list(shell.vfs.walk())
    files = sum(1 for item in nodes if not item.is_dir)
    shell.write(f"source: {source}")
    shell.write(f"directories: {len(nodes) - files}, files: {files}")
    shell.write(node.path())
    if node.is_dir:
        _print_tree(shell, node, "")


def _print_tree(shell, directory, indent):
    """Рекурсивно вывести содержимое каталога в виде дерева."""
    children = sorted(directory.children.values(), key=lambda n: n.name)
    for index, child in enumerate(children):
        last = index == len(children) - 1
        label = child.name + ("/" if child.is_dir else _file_note(child))
        shell.write(indent + (TREE_LAST if last else TREE_BRANCH) + label)
        if child.is_dir:
            _print_tree(shell, child,
                        indent + (TREE_SPACE if last else TREE_PIPE))


def _file_note(node):
    """Вернуть пометку о размере и типе содержимого файла."""
    kind = "binary, base64" if node.binary else "text"
    return f" ({node.size()} B, {kind})"
