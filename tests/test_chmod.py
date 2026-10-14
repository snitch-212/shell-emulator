"""Тесты команды chmod (этап 5)."""

import os
import tempfile
import unittest

from shell_emulator.commands.perms import apply_mode
from shell_emulator.errors import ShellError
from shell_emulator.vfs import load_zip
from tests.helpers import make_shell, run_lines
from tools.make_vfs import DEEP, write_archive


class ApplyModeTest(unittest.TestCase):
    """Вычисление новых прав по режиму."""

    def test_octal(self):
        """Восьмеричный режим заменяет права целиком."""
        self.assertEqual(apply_mode("755", 0o600), 0o755)
        self.assertEqual(apply_mode("0640", 0o777), 0o640)

    def test_symbolic(self):
        """Символьные режимы: +, -, =, списки и умолчание a."""
        cases = (("u+x", 0o644, 0o744), ("go-w", 0o666, 0o644),
                 ("a=r", 0o777, 0o444), ("+x", 0o644, 0o755),
                 ("u=rwx,g=rx,o=", 0o000, 0o750), ("ug+rw-x", 0o711,
                                                   0o661))
        for spec, before, after in cases:
            with self.subTest(spec=spec):
                self.assertEqual(apply_mode(spec, before), after)

    def test_invalid(self):
        """Неверные режимы вызывают ошибку."""
        for spec in ("abc", "999", "u+z", "", "u"):
            with self.subTest(spec=spec):
                with self.assertRaises(ShellError):
                    apply_mode(spec, 0)


class ChmodCommandTest(unittest.TestCase):
    """Команда chmod в оболочке."""

    def setUp(self):
        """Подготовить оболочку с VFS deep.zip."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.archive = os.path.join(tmp.name, "deep.zip")
        write_archive(self.archive, DEEP)
        self.shell = make_shell()
        self.shell.vfs = load_zip(self.archive)

    def mode(self, path):
        """Вернуть права узла VFS."""
        return self.shell.vfs.resolve(path).mode

    def test_changes_in_memory_only(self):
        """chmod меняет права в памяти, архив на диске не меняется."""
        before = os.stat(self.archive).st_mtime_ns
        run_lines(self.shell, "chmod 600 /etc/motd")
        self.assertEqual(self.mode("/etc/motd"), 0o600)
        self.assertEqual(os.stat(self.archive).st_mtime_ns, before)
        self.assertEqual(load_zip(self.archive).resolve("/etc/motd").mode,
                         0o644)

    def test_recursive_verbose(self):
        """-R применяет режим ко всему поддереву, -v сообщает."""
        out, _ = run_lines(self.shell, "chmod -Rv go= /projects/app/src")
        self.assertEqual(self.mode("/projects/app/src/utils/helpers.py"),
                         0o600)
        self.assertIn("mode of '/projects/app/src/main.py' changed from "
                      "0644 (rw-r--r--) to 0600 (rw-------)", out)

    def test_permissions_take_effect(self):
        """Снятые права мешают cd, ls и uniq."""
        _, err = run_lines(self.shell, "chmod -x /projects", "cd /projects",
                           "chmod u-r /var/log/syslog",
                           "uniq /var/log/syslog", "chmod 0 /etc",
                           "ls /etc")
        self.assertIn("cd: /projects: Permission denied", err)
        self.assertIn("uniq: /var/log/syslog: Permission denied", err)
        self.assertIn("ls: cannot access '/etc': Permission denied", err)

    def test_mode_starting_with_dash(self):
        """Режим вида -w не путается с опциями."""
        run_lines(self.shell, "chmod -w /etc/motd")
        self.assertEqual(self.mode("/etc/motd"), 0o444)

    def test_errors(self):
        """Ошибки chmod: нет операндов, неверный режим, нет файла."""
        status = self.shell.execute("chmod 644 /nope /etc/motd")
        _, err = run_lines(self.shell, "chmod", "chmod 755", "chmod q /etc")
        self.assertEqual(status, 1)
        self.assertIn("chmod: cannot access '/nope': No such file", err)
        self.assertIn("chmod: missing operand", err)
        self.assertIn("chmod: invalid mode: 'q'", err)

    def test_saved_with_vfs_save(self):
        """Новые права сохраняются командой vfs-save."""
        copy = os.path.join(os.path.dirname(self.archive), "copy.zip")
        run_lines(self.shell, "chmod 711 /projects/app/run.sh",
                  f"vfs-save {copy}")
        self.assertEqual(load_zip(copy).resolve("/projects/app/run.sh")
                         .mode, 0o711)
