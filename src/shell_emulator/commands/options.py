"""Разбор однобуквенных опций команд в стиле POSIX (-l, -la, --)."""

from ..errors import ShellError


def split_options(args, allowed):
    """Отделить опции от операндов.

    :param args: аргументы команды
    :param allowed: строка с допустимыми буквами опций, например "la"
    :return: кортеж (множество букв опций, список операндов)
    :raises ShellError: если встретилась недопустимая опция
    """
    flags = set()
    rest = list(args)
    while rest and rest[0].startswith("-") and rest[0] != "-":
        arg = rest.pop(0)
        if arg == "--":
            break
        for letter in arg[1:]:
            if letter not in allowed:
                raise ShellError(f"invalid option -- '{letter}'")
            flags.add(letter)
    return flags, rest
