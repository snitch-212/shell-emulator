"""Реестр команд эмулятора: имя команды -> функция (shell, args).

Функция команды выводит результат через shell.write, сообщает об
ошибке исключением ShellError и может вернуть код возврата.
"""

from .basic import cmd_exit
from .fs import cmd_cd, cmd_ls, cmd_pwd
from .perms import cmd_chmod
from .system import cmd_date
from .text import cmd_uniq
from .vfs_commands import cmd_vfs_info, cmd_vfs_save

COMMANDS = {
    "cd": cmd_cd,
    "chmod": cmd_chmod,
    "date": cmd_date,
    "exit": cmd_exit,
    "ls": cmd_ls,
    "pwd": cmd_pwd,
    "uniq": cmd_uniq,
    "vfs-info": cmd_vfs_info,
    "vfs-save": cmd_vfs_save,
}
