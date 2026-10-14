"""Системные команды: date."""

from datetime import datetime, timezone

from ..errors import ShellError
from .options import split_options

DEFAULT_FORMAT = "%a %b %d %H:%M:%S %Z %Y"
ISO_FORMAT = "%Y-%m-%d"
MAX_DATE_OPERANDS = 1


def cmd_date(shell, args):
    """Вывести текущие дату и время ОС: date [-u] [-I] [+ФОРМАТ].

    * -u — время UTC вместо местного;
    * -I — дата в формате ISO 8601 (ГГГГ-ММ-ДД);
    * +ФОРМАТ — формат strftime, например +%d.%m.%Y.
    """
    flags, operands = split_options(args, "uI")
    if len(operands) > MAX_DATE_OPERANDS:
        raise ShellError(f"extra operand '{operands[1]}'")
    fmt = ISO_FORMAT if "I" in flags else DEFAULT_FORMAT
    if operands:
        if not operands[0].startswith("+"):
            raise ShellError(f"invalid date '{operands[0]}'")
        fmt = operands[0][1:]
    now = datetime.now(timezone.utc)
    if "u" not in flags:
        now = now.astimezone()
    try:
        shell.write(now.strftime(fmt))
    except ValueError:
        raise ShellError(f"invalid format '{fmt}'") from None
