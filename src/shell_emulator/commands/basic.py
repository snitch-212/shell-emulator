"""Базовые команды: заглушки ls и cd, команда exit."""

from ..errors import ExitRequest, ShellError
from .options import split_options

EXIT_CODE_MODULO = 256
MAX_CD_ARGS = 1
MAX_EXIT_ARGS = 1


def cmd_ls(shell, args):
    """Заглушка ls: вывести имя команды и аргументы."""
    split_options(args, "la")
    shell.write(" ".join(["ls", *args]))


def cmd_cd(shell, args):
    """Заглушка cd: вывести имя команды и аргументы."""
    if len(args) > MAX_CD_ARGS:
        raise ShellError("too many arguments")
    shell.write(" ".join(["cd", *args]))


def cmd_exit(shell, args):
    """Завершить работу эмулятора: exit [код]."""
    if len(args) > MAX_EXIT_ARGS:
        raise ShellError("too many arguments")
    if not args:
        raise ExitRequest(shell.last_status)
    try:
        code = int(args[0])
    except ValueError:
        raise ShellError(f"{args[0]}: numeric argument required") from None
    raise ExitRequest(code % EXIT_CODE_MODULO)
