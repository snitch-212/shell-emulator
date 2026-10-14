"""Тесты параметров командной строки и стартового скрипта (этап 2)."""

import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

from shell_emulator.cli import main


def run_main(*argv, stdin=""):
    """Запустить main и вернуть (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with mock.patch("sys.stdin", io.StringIO(stdin)), \
            contextlib.redirect_stdout(out), \
            contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def write_script(test, text):
    """Создать временный файл скрипта и вернуть путь к нему."""
    handle, path = tempfile.mkstemp(suffix=".txt")
    with os.fdopen(handle, "w", encoding="utf-8") as file:
        file.write(text)
    test.addCleanup(os.remove, path)
    return path


class CliTest(unittest.TestCase):
    """Проверки запуска эмулятора с параметрами."""

    def test_debug_output(self):
        """При запуске выводятся все параметры."""
        code, out, _ = run_main("--script", "s.txt")
        self.assertEqual(code, 1)
        self.assertIn("--vfs     = (not set)", out)
        self.assertIn("--script  = s.txt", out)

    def test_missing_vfs(self):
        """Отсутствующий архив VFS — сообщение об ошибке и код 1."""
        code, out, err = run_main("--vfs", "no/such.zip")
        self.assertEqual(code, 1)
        self.assertIn("--vfs     = no/such.zip", out)
        self.assertIn("cannot load VFS 'no/such.zip'", err)

    def test_script_echoes_dialog(self):
        """Скрипт показывает приглашение, команду и её вывод."""
        path = write_script(self, "# note\nls -l\n\nexit 4\nls x\n")
        code, out, _ = run_main("--script", path)
        self.assertEqual(code, 4)
        self.assertIn("# note\n", out)
        self.assertRegex(out, r"\$ ls -l\nls -l\n")
        self.assertNotIn("ls x", out)

    def test_script_errors_have_line_numbers(self):
        """Ошибки скрипта выводятся с номером строки, скрипт идёт дальше."""
        path = write_script(self, "foo\ncd a b\nls ok\n")
        _, out, err = run_main("--script", path)
        self.assertIn(f"{path}: line 1: foo: command not found", err)
        self.assertIn(f"{path}: line 2: cd: too many arguments", err)
        self.assertIn("ls ok\n", out)

    def test_missing_script(self):
        """Отсутствующий скрипт — сообщение и код 1."""
        code, _, err = run_main("--script", "no/such/file.txt")
        self.assertEqual(code, 1)
        self.assertIn("cannot read script", err)

    def test_interactive_after_script(self):
        """После скрипта эмулятор читает команды пользователя."""
        path = write_script(self, "ls a\n")
        code, out, _ = run_main("--script", path, stdin="ls b\nexit 7\n")
        self.assertEqual(code, 7)
        self.assertIn("ls b", out)
