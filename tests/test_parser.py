"""Тесты разбора командной строки."""

import unittest

from shell_emulator.errors import ShellError
from shell_emulator.parser import parse_line

ENV = {"HOME": "/home/tester", "USER": "tester", "EMPTY": ""}


class ParseLineTest(unittest.TestCase):
    """Проверки функции parse_line."""

    def test_splits_words(self):
        """Слова разделяются любым количеством пробелов."""
        self.assertEqual(parse_line("ls   -l  /tmp", ENV),
                         ["ls", "-l", "/tmp"])

    def test_empty_line(self):
        """Пустая строка даёт пустой список."""
        self.assertEqual(parse_line("   ", ENV), [])

    def test_expands_variables(self):
        """Переменные $NAME и ${NAME} раскрываются."""
        self.assertEqual(parse_line("cd $HOME/${USER}x", ENV),
                         ["cd", "/home/tester/testerx"])

    def test_unknown_variable_is_empty(self):
        """Неизвестная переменная исчезает, как в bash."""
        self.assertEqual(parse_line("ls $NOPE", ENV), ["ls"])

    def test_single_quotes_are_literal(self):
        """В одинарных кавычках переменные не раскрываются."""
        self.assertEqual(parse_line("ls '$HOME a'", ENV),
                         ["ls", "$HOME a"])

    def test_double_quotes_expand(self):
        """В двойных кавычках переменные раскрываются, пробелы живут."""
        self.assertEqual(parse_line('ls "$HOME  x" ""', ENV),
                         ["ls", "/home/tester  x", ""])

    def test_escapes(self):
        """Обратная косая черта экранирует символ."""
        self.assertEqual(parse_line(r'ls a\ b \$HOME "q\"\$"', ENV),
                         ["ls", "a b", "$HOME", 'q"$'])

    def test_windows_paths(self):
        """Обратная косая черта в путях Windows не пропадает."""
        self.assertEqual(
            parse_line(r"vfs-save C:\Users\me\tmp\copy.zip build\a.zip",
                       ENV),
            ["vfs-save", r"C:\Users\me\tmp\copy.zip", r"build\a.zip"])

    def test_comment(self):
        """# в начале слова начинает комментарий."""
        self.assertEqual(parse_line("ls a#b # comment", ENV),
                         ["ls", "a#b"])

    def test_lonely_dollar(self):
        """Одиночный $ остаётся как есть."""
        self.assertEqual(parse_line("ls $ $1", ENV), ["ls", "$", "$1"])

    def test_unterminated_quotes(self):
        """Незакрытые кавычки — синтаксическая ошибка."""
        for line in ("ls 'abc", 'ls "abc', "ls abc\\"):
            with self.subTest(line=line):
                with self.assertRaises(ShellError):
                    parse_line(line, ENV)


if __name__ == "__main__":
    unittest.main()
