"""Реестр команд эмулятора: имя команды -> функция (shell, args)."""

from .basic import cmd_cd, cmd_exit, cmd_ls
from .vfs_commands import cmd_vfs_info, cmd_vfs_save

COMMANDS = {
    "cd": cmd_cd,
    "exit": cmd_exit,
    "ls": cmd_ls,
    "vfs-info": cmd_vfs_info,
    "vfs-save": cmd_vfs_save,
}
