"""Тесты ядра оболочки и цикла REPL (этап 1)."""

import unittest

from shell_emulator.shell import STATUS_NOT_FOUND
from tests.helpers import make_shell, run_lines


def feed(*lines):
    """Вернуть функцию ввода, выдающую строки, а затем EOF."""
    queue = list(lines)

    def read_line(prompt):
        """Вернуть следующую строку ввода."""
        del prompt
        if not queue:
            raise EOFError
        return queue.pop(0)
    return read_line


class ReplTest(unittest.TestCase):
    """Проверки приглашения, ошибок и команды exit."""

    def test_prompt_format(self):
        """Приглашение строится из имени пользователя и хоста."""
        shell = make_shell()
        self.assertRegex(shell.prompt(), r"^[^@]+@[^:]+:.+\$ $")

    def test_unknown_command(self):
        """Неизвестная команда — сообщение и код 127."""
        shell = make_shell()
        status = shell.execute("foo 1 2")
        self.assertEqual(status, STATUS_NOT_FOUND)
        self.assertIn("foo: command not found", shell.err.getvalue())

    def test_syntax_error(self):
        """Ошибка разбора выводится пользователю."""
        _, err = run_lines(make_shell(), "ls 'x")
        self.assertIn("syntax error", err)

    def test_exit_code(self):
        """exit N завершает цикл с кодом N."""
        shell = make_shell()
        self.assertEqual(shell.repl(feed("ls", "exit 3", "ls")), 3)

    def test_exit_errors(self):
        """exit с неверными аргументами не завершает работу."""
        shell = make_shell()
        code = shell.repl(feed("exit abc", "exit 1 2", "exit"))
        err = shell.err.getvalue()
        self.assertIn("numeric argument required", err)
        self.assertIn("too many arguments", err)
        self.assertEqual(code, 1)

    def test_eof_exits(self):
        """Конец ввода (Ctrl+D) завершает работу."""
        self.assertEqual(make_shell().repl(feed()), 0)
