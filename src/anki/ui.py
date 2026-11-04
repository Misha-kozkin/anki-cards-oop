import textwrap
from typing import ClassVar


class TextUI:
    """Взаимодействие с пользователем через консоль."""

    MENU: ClassVar[str] = textwrap.dedent("""\
        Меню:
            1. Начать игру
            2. Добавить слова
            3. Тренировка до первой ошибки
            4. Вывод всех слов
            5. Выход
        """)
