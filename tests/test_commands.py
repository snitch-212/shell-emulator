"""Тесты основных команд: ls, cd, pwd, uniq, date (этап 4)."""

import os
import re
import tempfile
import unittest

from shell_emulator.vfs import load_zip
from tests.helpers import make_shell, run_lines
from tools.make_vfs import DEEP, write_archive


def deep_shell(test):
    """Создать оболочку с VFS из архива deep.zip."""
    tmp = tempfile.TemporaryDirectory()
    test.addCleanup(tmp.cleanup)
    path = os.path.join(tmp.name, "deep.zip")
    write_archive(path, DEEP)
    shell = make_shell()
    shell.vfs = load_zip(path)
    return shell


class NavigationTest(unittest.TestCase):
    """Команды ls, cd и pwd."""

    def setUp(self):
        """Подготовить оболочку с VFS deep.zip."""
        self.shell = deep_shell(self)

    def test_ls_root(self):
        """ls без аргументов выводит текущий каталог."""
        out, _ = run_lines(self.shell, "ls")
        self.assertEqual(out, "etc  home  projects  var\n")

    def test_ls_long(self):
        """ls -l выводит права, размер и имя."""
        out, _ = run_lines(self.shell, "ls -l /projects/app")
        self.assertRegex(out, r"-rwxr-xr-x +1 \S+ \S+ +30 .* run\.sh\n")
        self.assertRegex(out, r"drwxr-xr-x .* src\n")

    def test_ls_all_and_file(self):
        """ls -a показывает . и .., файл выводится по имени."""
        out, _ = run_lines(self.shell, "ls -a /etc", "ls /etc/motd")
        self.assertEqual(out, ".  ..  motd\n/etc/motd\n")

    def test_ls_errors(self):
        """Несуществующий путь — ошибка и код 1, остальные выводятся."""
        status = self.shell.execute("ls /nope /etc")
        self.assertEqual(status, 1)
        self.assertIn("ls: cannot access '/nope': No such file",
                      self.shell.err.getvalue())
        self.assertIn("/etc:\nmotd\n", self.shell.out.getvalue())

    def test_cd_and_pwd(self):
        """cd меняет каталог, pwd и приглашение это отражают."""
        out, _ = run_lines(self.shell, "cd projects/app/src", "pwd",
                           "cd ../../..", "pwd", "cd -")
        self.assertEqual(out, "/projects/app/src\n/\n/projects/app/src\n")
        self.assertIn(":/projects/app/src$", self.shell.prompt())

    def test_cd_errors(self):
        """cd в файл, в несуществующий путь, лишние аргументы."""
        _, err = run_lines(self.shell, "cd /etc/motd", "cd /nope",
                           "cd a b", "cd -", "pwd x")
        self.assertIn("cd: /etc/motd: Not a directory", err)
        self.assertIn("cd: /nope: No such file or directory", err)
        self.assertIn("cd: too many arguments", err)
        self.assertIn("cd: OLDPWD not set", err)
        self.assertIn("pwd: too many arguments", err)

    def test_cd_home(self):
        """cd без аргументов и cd ~ переходят в домашний каталог."""
        shell = make_shell()
        run_lines(shell, "cd /etc", "cd", "pwd", "cd /", "cd ~/projects")
        self.assertEqual(shell.out.getvalue(), f"/home/{shell.user}\n")
        self.assertEqual(shell.prompt()[-len("~/projects$ "):],
                         "~/projects$ ")


class UniqTest(unittest.TestCase):
    """Команда uniq."""

    def setUp(self):
        """Подготовить оболочку с VFS deep.zip."""
        self.shell = deep_shell(self)

    def uniq(self, options):
        """Выполнить uniq с опциями над /var/log/syslog."""
        self.shell.out.seek(0)
        self.shell.out.truncate()
        out, _ = run_lines(self.shell, f"uniq {options} /var/log/syslog")
        return out

    def test_modes(self):
        """Все режимы uniq: обычный, -c, -d, -u."""
        self.assertEqual(self.uniq(""), "boot\nstart\nstop\n")
        self.assertEqual(self.uniq("-c"),
                         "      2 boot\n      3 start\n      1 stop\n")
        self.assertEqual(self.uniq("-d"), "boot\nstart\n")
        self.assertEqual(self.uniq("-u"), "stop\n")

    def test_ignore_case(self):
        """-i сравнивает строки без учёта регистра."""
        out, _ = run_lines(make_shell(), "uniq -ic fruits.txt")
        self.assertEqual(out, "      2 apple\n      1 banana\n"
                              "      2 Apple\n      1 cherry\n")

    def test_errors(self):
        """Ошибки uniq: нет операнда, каталог, лишний операнд."""
        _, err = run_lines(self.shell, "uniq", "uniq /etc", "uniq a b",
                           "uniq /nope", "uniq -x /etc/motd")
        for text in ("missing operand", "/etc: Is a directory",
                     "extra operand 'b'", "/nope: No such file",
                     "invalid option -- 'x'"):
            self.assertIn(text, err)


class DateTest(unittest.TestCase):
    """Команда date."""

    def test_formats(self):
        """date, date -I, date -u +ФОРМАТ."""
        out, _ = run_lines(make_shell(), "date", "date -I",
                           "date -u +%Z:%Y")
        lines = out.splitlines()
        self.assertRegex(lines[0], r"^\w{3} \w{3} \d{2} \d\d:\d\d:\d\d ")
        self.assertRegex(lines[1], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(re.fullmatch(r"UTC:\d{4}", lines[2]))

    def test_errors(self):
        """Неверный операнд и лишний операнд."""
        _, err = run_lines(make_shell(), "date foo", "date +%Y +%m")
        self.assertIn("date: invalid date 'foo'", err)
        self.assertIn("date: extra operand '+%m'", err)
