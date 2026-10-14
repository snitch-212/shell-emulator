"""Базовые команды оболочки: exit."""

from ..errors import ExitRequest, ShellError

EXIT_CODE_MODULO = 256
MAX_EXIT_ARGS = 1


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
