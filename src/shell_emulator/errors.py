"""Исключения эмулятора командной оболочки."""


class ShellError(Exception):
    """Ошибка выполнения команды; текст выводится пользователю."""


class ExitRequest(Exception):
    """Запрос на завершение работы эмулятора (команда exit)."""

    def __init__(self, code=0):
        """Сохранить код завершения процесса."""
        super().__init__(code)
        self.code = code
