"""Реестр команд эмулятора: имя команды -> функция (shell, args)."""

from .basic import cmd_cd, cmd_exit, cmd_ls

COMMANDS = {
    "cd": cmd_cd,
    "exit": cmd_exit,
    "ls": cmd_ls,
}
