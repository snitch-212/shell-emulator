"""Тесты команд-заглушек этапа 1."""

import unittest

from tests.helpers import make_shell, run_lines


class StubTest(unittest.TestCase):
    """Заглушки ls и cd выводят своё имя и аргументы."""

    def test_ls_stub(self):
        """ls печатает аргументы с раскрытыми переменными."""
        out, _ = run_lines(make_shell(), "ls -l $HOME")
        self.assertEqual(out, "ls -l /home/tester\n")

    def test_cd_stub(self):
        """cd печатает аргумент."""
        out, _ = run_lines(make_shell(), "cd /tmp")
        self.assertEqual(out, "cd /tmp\n")

    def test_bad_arguments(self):
        """Неверные аргументы приводят к сообщению об ошибке."""
        _, err = run_lines(make_shell(), "ls -z", "cd a b")
        self.assertIn("ls: invalid option -- 'z'", err)
        self.assertIn("cd: too many arguments", err)
