"""Разбор командной строки: слова, кавычки, экранирование, переменные.

Поддерживается подмножество синтаксиса POSIX shell:

* слова разделяются пробельными символами;
* ``'...'`` — текст без каких-либо подстановок;
* ``"..."`` — текст с подстановкой переменных,
  внутри работают экранирования ``\\"``, ``\\\\`` и ``\\$``;
* ``\\`` вне кавычек экранирует только пробел, кавычки, ``$``, ``#``
  и сам ``\\``; перед остальными символами он остаётся как есть,
  поэтому пути Windows (``build\\copy.zip``) работают без кавычек;
* ``$NAME`` и ``${NAME}`` — значение переменной окружения
  реальной ОС (неизвестная переменная даёт пустую строку);
* ``#`` в начале слова — комментарий до конца строки.
"""

import os
import re

from .errors import ShellError

NAME = r"[A-Za-z_][A-Za-z0-9_]*"
VAR_PATTERN = re.compile(r"\$(?:\{(" + NAME + r")\}|(" + NAME + r"))")
DOUBLE_QUOTE_ESCAPES = frozenset('"\\$')
UNQUOTED_ESCAPES = frozenset(" \t'\"\\$#")
NOT_FOUND = -1


def parse_line(line, env=None):
    """Разбить строку на список слов с раскрытием переменных.

    :param line: строка, введённая пользователем
    :param env: словарь переменных окружения (по умолчанию os.environ)
    :return: список слов; пустой, если строка пустая или комментарий
    :raises ShellError: при незакрытой кавычке или висящем ``\\``
    """
    env = os.environ if env is None else env
    return _Tokenizer(line, env).run()


class _Tokenizer:
    """Конечный автомат, последовательно читающий строку."""

    def __init__(self, line, env):
        """Подготовить автомат к разбору строки ``line``."""
        self.line = line
        self.env = env
        self.pos = 0
        self.words = []
        self.current = None

    def run(self):
        """Прочитать всю строку и вернуть список слов."""
        while self.pos < len(self.line):
            char = self.line[self.pos]
            if char.isspace():
                self._finish_word()
                self.pos += 1
            elif char == "#" and self.current is None:
                break
            else:
                self._read_part(char)
        self._finish_word()
        return self.words

    def _read_part(self, char):
        """Выбрать обработчик для очередного фрагмента слова."""
        handlers = {
            "'": self._read_single,
            '"': self._read_double,
            "\\": self._read_escape,
            "$": self._read_var,
        }
        handlers.get(char, self._read_char)()

    def _append(self, text):
        """Дописать текст к текущему слову (и начать слово)."""
        self.current = (self.current or "") + text

    def _finish_word(self):
        """Завершить текущее слово, если оно начато."""
        if self.current is not None:
            self.words.append(self.current)
            self.current = None

    def _read_char(self):
        """Прочитать обычный символ."""
        self._append(self.line[self.pos])
        self.pos += 1

    def _read_single(self):
        """Прочитать строку в одинарных кавычках без подстановок."""
        start = self.pos + 1
        end = self.line.find("'", start)
        if end == NOT_FOUND:
            raise ShellError("syntax error: unterminated quote (')")
        self._append(self.line[start:end])
        self.pos = end + 1

    def _read_double(self):
        """Прочитать строку в двойных кавычках с подстановками."""
        self._append("")
        self.pos += 1
        while self._char_in_quotes() != '"':
            following = self.line[self.pos + 1:self.pos + 2]
            if self.line[self.pos] == "$":
                self._read_var()
            elif self.line[self.pos] == "\\" and \
                    following in DOUBLE_QUOTE_ESCAPES:
                self._append(following)
                self.pos += 2
            else:
                self._read_char()
        self.pos += 1

    def _char_in_quotes(self):
        """Вернуть текущий символ внутри двойных кавычек."""
        if self.pos >= len(self.line):
            raise ShellError('syntax error: unterminated quote (")')
        return self.line[self.pos]

    def _read_escape(self):
        """Прочитать экранированный символ вне кавычек."""
        following = self.line[self.pos + 1:self.pos + 2]
        if not following:
            raise ShellError("syntax error: unexpected end after '\\'")
        if following in UNQUOTED_ESCAPES:
            self._append(following)
            self.pos += 2
        else:
            self._append("\\")
            self.pos += 1

    def _read_var(self):
        """Подставить значение переменной окружения."""
        match = VAR_PATTERN.match(self.line, self.pos)
        if match is None:
            self._read_char()
            return
        value = self.env.get(match.group(1) or match.group(2), "")
        if value:
            self._append(value)
        self.pos = match.end()
