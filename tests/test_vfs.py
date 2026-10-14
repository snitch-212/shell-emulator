"""Тесты виртуальной файловой системы (этап 3)."""

import os
import tempfile
import unittest
import zipfile

from shell_emulator.errors import ShellError
from shell_emulator.vfs import (VfsError, default_vfs, load_zip,
                                save_zip)
from tests.helpers import make_shell, run_lines
from tools.make_vfs import BINARY_DATA, DEEP, write_archive


class VfsTest(unittest.TestCase):
    """Загрузка, обход и сохранение VFS."""

    def setUp(self):
        """Создать временный каталог и архив deep.zip в нём."""
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.deep = self.path("deep.zip")
        write_archive(self.deep, DEEP)

    def path(self, name):
        """Вернуть путь к файлу во временном каталоге."""
        return os.path.join(self.tmp.name, name)

    def test_load_tree(self):
        """Дерево и права доступа берутся из архива."""
        vfs = load_zip(self.deep)
        helpers = vfs.resolve("/projects/app/src/utils/helpers.py")
        self.assertEqual(helpers.to_bytes(), b"def f():\n    pass\n")
        self.assertEqual(vfs.resolve("/projects/app/run.sh").mode, 0o755)
        self.assertTrue(vfs.resolve("/home/student/projects").is_dir)

    def test_binary_is_base64(self):
        """Двоичные данные хранятся в base64 и восстанавливаются."""
        icon = load_zip(self.deep).resolve("/projects/app/assets/icon.bin")
        self.assertTrue(icon.binary)
        self.assertNotIn("\x89", icon.content)
        self.assertEqual(icon.to_bytes(), BINARY_DATA)

    def test_relative_paths(self):
        """Работают относительные пути, . и .."""
        vfs = load_zip(self.deep)
        vfs.cwd = vfs.resolve("/projects/app/src")
        self.assertEqual(vfs.resolve("../docs/./guide.md").path(),
                         "/projects/app/docs/guide.md")
        self.assertIs(vfs.resolve("/../.."), vfs.root)

    def test_resolve_errors(self):
        """Несуществующий путь и путь через файл — ошибки."""
        vfs = load_zip(self.deep)
        with self.assertRaisesRegex(ShellError, "No such file"):
            vfs.resolve("/nope")
        with self.assertRaisesRegex(ShellError, "Not a directory"):
            vfs.resolve("/etc/motd/x")

    def test_load_errors(self):
        """Ошибки загрузки: нет файла, не ZIP, каталог."""
        broken = self.path("broken.zip")
        with open(broken, "w", encoding="utf-8") as file:
            file.write("not a zip")
        for path, reason in ((self.path("none.zip"), "No such file"),
                             (broken, "invalid format"),
                             (self.tmp.name, "cannot load VFS")):
            with self.subTest(path=path):
                with self.assertRaisesRegex(VfsError, reason):
                    load_zip(path)

    def test_source_is_not_modified(self):
        """Загрузка не изменяет архив на диске."""
        before = os.stat(self.deep).st_mtime_ns
        vfs = load_zip(self.deep)
        vfs.resolve("/etc/motd").set_bytes(b"changed")
        self.assertEqual(os.stat(self.deep).st_mtime_ns, before)

    def test_save_round_trip(self):
        """vfs-save сохраняет файлы, каталоги и права доступа."""
        vfs = load_zip(self.deep)
        copy = self.path("copy.zip")
        save_zip(vfs, copy)
        loaded = load_zip(copy)
        self.assertEqual([n.path() for n in loaded.walk()],
                         [n.path() for n in vfs.walk()])
        self.assertEqual(loaded.resolve("/projects/app/run.sh").mode,
                         0o755)
        with zipfile.ZipFile(copy) as archive:
            self.assertIsNone(archive.testzip())

    def test_default_vfs(self):
        """VFS по умолчанию содержит домашний каталог пользователя."""
        vfs = default_vfs("alice")
        self.assertEqual(vfs.cwd.path(), "/home/alice")
        self.assertIsNone(vfs.source)


class VfsCommandsTest(unittest.TestCase):
    """Команды vfs-save и vfs-info."""

    def test_vfs_save_errors(self):
        """vfs-save без пути и с неверным путём сообщает об ошибке."""
        _, err = run_lines(make_shell(), "vfs-save",
                           "vfs-save /no/such/dir/x.zip", "vfs-save a b")
        self.assertIn("vfs-save: missing operand", err)
        self.assertIn("vfs-save: cannot save VFS", err)
        self.assertIn("vfs-save: too many arguments", err)

    def test_vfs_info(self):
        """vfs-info показывает источник и дерево."""
        out, _ = run_lines(make_shell(), "vfs-info")
        self.assertIn("source: (default VFS in memory)", out)
        self.assertIn("fruits.txt (38 B, text)", out)
