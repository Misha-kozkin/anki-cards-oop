"""Текстовый интерфейс игры Anki для работы в консоли."""

import textwrap
from typing import ClassVar

from anki.anki import Anki


class TextUI:
    """Отвечает за общение с пользователем через консоль.

    Показывает меню, читает ввод и выводит результаты. Вся логика
    игры (слова, проверка переводов) находится в объекте Anki,
    который передаётся при создании интерфейса.

    Attributes:
        MENU: Текст главного меню игры, общий для всех экземпляров.
        STOP_WORD: Слово для выхода из игры и из добавления слов.
    """

    MENU: ClassVar[str] = textwrap.dedent("""\
        Меню:
            1. Начать игру
            2. Добавить слова
            3. Тренировка до первой ошибки
            4. Вывод всех слов
            5. Выход
        """)

    STOP_WORD: ClassVar[str] = 'СТОП'

    def __init__(self, anki_game: Anki) -> None:
        """Связывает интерфейс с игрой.

        Args:
            anki_game: Объект игры, с которым работает интерфейс.
        """
        self._anki_game: Anki = anki_game

    def _is_stop_word(self, text: str) -> bool:
        """Проверяет, ввёл ли пользователь слово для выхода.

        Args:
            text: Строка, которую ввёл пользователь.

        Returns:
            True, если это STOP_WORD без учёта регистра и пробелов.
        """
        return text.strip().lower() == self.STOP_WORD.lower()

    def start_game(self) -> None:
        """Запускает тренировку: случайные слова до ввода STOP_WORD."""
        print(f'Чтобы закончить, введите {self.STOP_WORD}')
        while True:
            try:
                word = self._anki_game.get_random_word()
            except ValueError as error:
                print(error)
                break
            print(f'Ваше слово: {word}')
            answer = input('Ваш перевод: ')
            if self._is_stop_word(answer):
                break
            if self._anki_game.check_translation(word, answer):
                print('Верно!')
            else:
                correct = self._anki_game.get_translation(word)
                print(f'Неправильно, правильный ответ: {correct}')

    def train_until_mistake(self) -> None:
        """Тренировка до первой ошибки или до ввода STOP_WORD.

        В конце выводит количество правильных ответов и время игры.
        """
        print(
            'Режим: игра до первой ошибки! '
            f'Чтобы выйти вручную, введите {self.STOP_WORD}'
        )
        self._anki_game.start_session()
        while True:
            try:
                word = self._anki_game.get_random_word()
            except ValueError as error:
                print(error)
                self._anki_game.end_session()
                break
            print(f'Ваше слово: {word}')
            answer = input('Ваш перевод: ')
            if self._is_stop_word(answer):
                self._anki_game.end_session()
                print('Выход из режима по запросу пользователя.')
                break
            if self._anki_game.check_translation(word, answer):
                print('Верно!')
            else:
                correct = self._anki_game.get_translation(word)
                print(f'Ошибка! Правильный ответ: {correct}')
                break
        stats = self._anki_game.last_session_stats
        total_time = format(stats['total_time'], '.2f')
        print(f'Правильных ответов: {stats["correct_answers"]}')
        print(f'Время игры: {total_time} секунд')

    def add_words(self) -> None:
        """Добавляет слова в игру, пока пользователь не введёт STOP_WORD.

        Пустые значения и значения с запятой не добавляются:
        запятая разделяет слово и перевод в файле со словами.
        """
        print(f'Чтобы закончить, введите {self.STOP_WORD}')
        while True:
            word = input('Введите слово: ')
            if self._is_stop_word(word):
                break
            translation = input('Введите перевод: ')
            if self._is_stop_word(translation):
                break
            if not word.strip() or not translation.strip():
                print('Слово и перевод не должны быть пустыми.')
                continue
            if ',' in word or ',' in translation:
                print('Слово и перевод не должны содержать запятую.')
                continue
            self._anki_game.add_word(word, translation)

    def show_words(self) -> None:
        """Выводит количество слов и все пары «слово - перевод»."""
        print(f'Всего слов: {len(self._anki_game)}')
        for word, translation in self._anki_game:
            print(f'{word} - {translation}')

    def main_loop(self) -> None:
        """Показывает меню и выполняет выбранные пункты до выбора «Выход»."""
        while True:
            print(self.MENU)
            choice = input('Пункт меню: ').strip()
            if choice == '1':
                self.start_game()
            elif choice == '2':
                self.add_words()
            elif choice == '3':
                self.train_until_mistake()
            elif choice == '4':
                self.show_words()
            elif choice == '5':
                break
            else:
                print('Неизвестный пункт меню')
