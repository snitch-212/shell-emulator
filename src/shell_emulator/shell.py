"""Ядро эмулятора: приглашение, выполнение команд и цикл REPL."""

import getpass
import os
import socket
import sys

from .commands import COMMANDS
from .errors import ExitRequest, ShellError
from .parser import parse_line
from .vfs import default_vfs

STATUS_OK = 0
STATUS_ERROR = 1
STATUS_NOT_FOUND = 127
STATUS_INTERRUPTED = 130


class Shell:
    """Эмулятор командной оболочки.

    Вывод команд направляется в ``out``, сообщения об ошибках — в
    ``err``, что позволяет подменять потоки в тестах.
    """

    def __init__(self, out=None, err=None, env=None, vfs=None):
        """Создать оболочку с потоками вывода, окружением и VFS."""
        self.out = out or sys.stdout
        self.err = err or sys.stderr
        self.env = os.environ if env is None else env
        self.user = getpass.getuser()
        self.host = socket.gethostname()
        self.vfs = vfs or default_vfs(self.user)
        self.commands = dict(COMMANDS)
        self.last_status = STATUS_OK
        self.location = ""

    def write(self, text=""):
        """Вывести строку текста в поток вывода."""
        print(text, file=self.out)

    def error(self, message):
        """Вывести сообщение об ошибке в поток ошибок."""
        self.out.flush()
        print(message, file=self.err)
        self.err.flush()

    def home_dir(self):
        """Вернуть путь домашнего каталога пользователя в VFS."""
        return f"/home/{self.user}"

    def cwd_display(self):
        """Вернуть текущий каталог VFS для приглашения (~ — домашний)."""
        path = self.vfs.cwd.path()
        home = self.vfs.home
        if home != "/" and (path == home or path.startswith(home + "/")):
            return "~" + path[len(home):]
        return path

    def prompt(self):
        """Сформировать приглашение вида user@host:~$."""
        return f"{self.user}@{self.host}:{self.cwd_display()}$ "

    def execute(self, line):
        """Разобрать и выполнить одну строку; вернуть код возврата.

        :raises ExitRequest: если выполнена команда exit
        """
        try:
            words = parse_line(line, self.env)
        except ShellError as exc:
            return self._fail(f"shell: {exc}", STATUS_ERROR)
        if not words:
            return self.last_status
        name, args = words[0], words[1:]
        handler = self.commands.get(name)
        if handler is None:
            return self._fail(f"{name}: command not found",
                              STATUS_NOT_FOUND)
        try:
            handler(self, args)
        except ShellError as exc:
            return self._fail(f"{name}: {exc}", STATUS_ERROR)
        self.last_status = STATUS_OK
        return STATUS_OK

    def _fail(self, message, status):
        """Сообщить об ошибке и запомнить код возврата."""
        self.error(self.location + message)
        self.last_status = status
        return status

    def run_script(self, path):
        """Выполнить стартовый скрипт, отображая ввод и вывод.

        Ошибки в отдельных строках выводятся с указанием номера
        строки, после чего выполнение скрипта продолжается.

        :raises ShellError: если файл скрипта нельзя прочитать
        :raises ExitRequest: если в скрипте выполнена команда exit
        """
        try:
            with open(path, encoding="utf-8") as file:
                lines = file.read().splitlines()
        except (OSError, UnicodeDecodeError) as exc:
            reason = getattr(exc, "strerror", None) or exc
            raise ShellError(f"cannot read script '{path}': {reason}") \
                from None
        for number, line in enumerate(lines, start=1):
            self._run_script_line(f"{path}: line {number}: ", line)

    def _run_script_line(self, location, line):
        """Показать строку скрипта как ввод пользователя и выполнить."""
        stripped = line.strip()
        if not stripped:
            return
        if stripped.startswith("#"):
            self.write(line)
            return
        self.write(self.prompt() + line)
        self.location = location
        try:
            self.execute(line)
        finally:
            self.location = ""

    def repl(self, read_line=input, echo=False):
        """Запустить интерактивный цикл; вернуть код завершения.

        :param read_line: функция чтения строки с приглашением
        :param echo: повторять введённую строку (ввод не с терминала)
        """
        while True:
            try:
                line = read_line(self.prompt())
                if echo:
                    self.write(line)
            except EOFError:
                self.write()
                return self.last_status
            except KeyboardInterrupt:
                self.write("^C")
                self.last_status = STATUS_INTERRUPTED
                continue
            try:
                self.execute(line)
            except ExitRequest as request:
                return request.code
