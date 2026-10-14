"""Интерфейс командной строки эмулятора."""

from .shell import Shell


def main(argv=None):
    """Запустить эмулятор и вернуть код завершения процесса."""
    del argv
    shell = Shell()
    return shell.repl()
