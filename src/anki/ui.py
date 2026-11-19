"""Текстовый интерфейс игры Anki для работы в консоли."""

from typing import Callable, ClassVar

from anki.anki import Anki


class TextUI:
    """Отвечает за общение с пользователем через консоль.

    Показывает меню, читает ввод и выводит результаты. Вся логика
    игры (слова, проверка переводов) находится в объекте Anki,
    который передаётся при создании интерфейса.

    Меню строится заново перед каждым выбором: пункты, которым
    нужны слова, скрыты, пока в игре нет слов.

    Attributes:
        STOP_WORD: Слово для выхода из игры и из добавления слов.
    """

    STOP_WORD: ClassVar[str] = 'СТОП'

    def __init__(self, anki_game: Anki) -> None:
        """Связывает интерфейс с игрой.

        Args:
            anki_game: Объект игры, с которым работает интерфейс.
        """
        self._anki_game: Anki = anki_game
        self._is_running: bool = False
        # Команды меню: (обработчик, текст пункта, условие видимости).
        self._command_definition: list[
            tuple[Callable[[], None], str, Callable[[], bool]]
        ] = [
            (self.start_game, 'Начать игру', self._has_words),
            (self.add_words, 'Добавить слова', lambda: True),
            (
                self.train_until_mistake,
                'Тренировка до первой ошибки',
                self._has_words,
            ),
            (self.find_translation, 'Найти перевод', self._has_words),
            (self.show_words, 'Вывод всех слов', self._has_words),
            (self.stop, 'Выход', lambda: True),
        ]

    def _has_words(self) -> bool:
        """Проверяет, есть ли в игре слова.

        Returns:
            True, если в игре есть хотя бы одно слово.
        """
        return len(self._anki_game) > 0

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

    def find_translation(self) -> None:
        """Спрашивает слово и выводит его перевод, если слово есть в игре."""
        word = input('Введите слово для поиска: ')
        if word in self._anki_game:
            translation = self._anki_game.get_translation(word)
            print(f'Перевод: {translation}')
        else:
            print(f'Слова «{word.strip()}» нет в игре')

    def stop(self) -> None:
        """Останавливает главный цикл меню."""
        self._is_running = False

    def get_available_commands(self) -> list[tuple[Callable[[], None], str]]:
        """Возвращает команды, которые сейчас можно показать в меню.

        Returns:
            Список пар (обработчик, текст пункта) в порядке меню.
        """
        commands: list[tuple[Callable[[], None], str]] = []
        for func, description, is_visible in self._command_definition:
            if is_visible():
                commands.append((func, description))
        return commands

    def main_loop(self) -> None:
        """Показывает меню и выполняет выбранные пункты до выбора «Выход».

        Номера пунктов присваиваются по порядку доступных команд.
        """
        self._is_running = True
        while self._is_running:
            commands: dict[str, Callable[[], None]] = {}
            menu_lines: list[str] = ['Меню:']
            for number, (func, description) in enumerate(
                self.get_available_commands(), start=1
            ):
                commands[str(number)] = func
                menu_lines.append(f'    {number}. {description}')
            print('\n'.join(menu_lines))
            choice = input('Пункт меню: ').strip()
            if choice in commands:
                commands[choice]()
            else:
                print('Неизвестный пункт меню')
            print()
