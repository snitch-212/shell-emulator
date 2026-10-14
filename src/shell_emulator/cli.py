"""Интерфейс командной строки эмулятора: параметры и запуск."""

import argparse
import sys

from .errors import ExitRequest, ShellError
from .shell import STATUS_ERROR, Shell
from .vfs import load_zip


def build_parser():
    """Создать парсер параметров командной строки."""
    parser = argparse.ArgumentParser(
        prog="shell_emulator",
        description="Эмулятор командной оболочки UNIX-подобной ОС.")
    parser.add_argument("--vfs", metavar="PATH",
                        help="путь к физическому расположению VFS")
    parser.add_argument("--script", metavar="PATH",
                        help="путь к стартовому скрипту")
    return parser


def print_config(args, shell):
    """Вывести отладочную информацию о заданных параметрах."""
    shell.write("[debug] emulator parameters:")
    for name, value in vars(args).items():
        shell.write(f"[debug]   --{name:<7} = {value or '(not set)'}")


def start(args, shell):
    """Загрузить VFS, выполнить стартовый скрипт и запустить REPL."""
    if args.vfs:
        shell.vfs = load_zip(args.vfs, home=shell.home_dir())
    if args.script:
        shell.run_script(args.script)
    return shell.repl(echo=not sys.stdin.isatty())


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения процесса."""
    args = build_parser().parse_args(argv)
    shell = Shell()
    print_config(args, shell)
    try:
        return start(args, shell)
    except ShellError as exc:
        shell.error(f"shell: {exc}")
        return STATUS_ERROR
    except ExitRequest as request:
        return request.code
