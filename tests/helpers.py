"""Вспомогательные функции для тестов."""

import io

from shell_emulator.shell import Shell


def make_shell(env=None, **kwargs):
    """Создать оболочку, пишущую вывод и ошибки в строковые буферы."""
    env = {"HOME": "/home/tester", "USER": "tester"} if env is None else env
    return Shell(out=io.StringIO(), err=io.StringIO(), env=env, **kwargs)


def run_lines(shell, *lines):
    """Выполнить строки и вернуть кортеж (stdout, stderr)."""
    for line in lines:
        shell.execute(line)
    return shell.out.getvalue(), shell.err.getvalue()
