"""Основная логика игры Anki: хранение слов и их нормализация."""

import random

from typing import Optional


class Anki:
    """Хранит словарь игры и следит за единым форматом слов.

    Все слова и переводы хранятся нормализованными: без пробелов
    по краям и в нижнем регистре. Класс не зависит от способа
    ввода-вывода и источника слов, поэтому его можно использовать
    в консольной, графической или веб-версии игры.
    """

    def __init__(self, *, words: Optional[dict[str, str]] = None) -> None:
        """Создаёт игру и добавляет в неё начальные слова.

        Args:
            words: Словарь {слово: перевод}. Ключи и значения
                нормализуются. Если не передан, игра начинается
                с пустым словарём.

        Raises:
            ValueError: Если words не словарь или в нём есть
                ключи или значения, которые не являются строками.
        """
        if words is None:
            words = {}
        if not isinstance(words, dict):
            raise ValueError('Параметр words должен быть словарём')
        self._words: dict[str, str] = {}
        for word, translation in words.items():
            self.add_word(word, translation)

    @staticmethod
    def normalize_word(word: str) -> str:
        """Убирает пробелы по краям и приводит слово к нижнему регистру.

        Args:
            word: Слово для нормализации.

        Returns:
            Нормализованное слово.

        Raises:
            ValueError: Если word не является строкой.
        """
        if not isinstance(word, str):
            raise ValueError(
                f'Слово должно быть строкой, получено: {type(word).__name__}'
            )
        return word.strip().lower()

    def add_word(self, word: str, translation: str) -> None:
        """Добавляет в словарь слово и его перевод.

        Оба значения нормализуются через normalize_word. Если слово
        уже есть в словаре, его перевод заменяется новым.

        Args:
            word: Слово, которое нужно перевести.
            translation: Перевод слова.

        Raises:
            ValueError: Если word или translation не является строкой.
        """
        normalized_word = self.normalize_word(word)
        normalized_translation = self.normalize_word(translation)
        self._words[normalized_word] = normalized_translation

    def get_words(self) -> dict[str, str]:
        """Возвращает копию словаря со словами.

        Изменение возвращённого словаря не влияет на слова игры.
        Чтобы добавить слово, используйте add_word.

        Returns:
            Новый словарь {слово: перевод}.
        """
        return self._words.copy()

    def __contains__(self, word: str) -> bool:
        """Проверяет, есть ли слово в игре (оператор in).

        Слово нормализуется перед поиском, поэтому регистр и пробелы
        по краям не важны.

        Args:
            word: Слово, которое нужно найти.

        Returns:
            True, если слово есть в словаре, иначе False.

        Raises:
            ValueError: Если word не является строкой.

        Examples:
            >>> anki = Anki(words={'Python': 'Питон'})
            >>> 'PYTHON' in anki
            True
            >>> 'TypeScript' in anki
            False
        """
        return self.normalize_word(word) in self._words

    def __str__(self) -> str:
        """Возвращает описание колоды для print() и str().

        Returns:
            Строка с количеством слов в колоде.

        Examples:
            >>> print(Anki(words={'cat': 'кот', 'dog': 'собака'}))
            Колода Anki, слов в колоде: 2
        """
        return f'Колода Anki, слов в колоде: {len(self._words)}'

    def get_random_word(self) -> str:
        """Выбирает случайное слово из игры.

        Returns:
            Случайное слово (без перевода).

        Raises:
            ValueError: Если в игре нет ни одного слова.
        """
        if not self._words:
            raise ValueError('В игре нет слов. Сначала добавьте слова.')
        return random.choice(list(self._words))

    def get_translation(self, word: str) -> str:
        """Возвращает перевод слова.

        Args:
            word: Слово, перевод которого нужен. Нормализуется
                перед поиском.

        Returns:
            Перевод слова.

        Raises:
            ValueError: Если word не строка или такого слова нет в игре.
        """
        normalized_word = self.normalize_word(word)
        if normalized_word not in self._words:
            raise ValueError(f'Слова «{normalized_word}» нет в игре')
        return self._words[normalized_word]

    def check_translation(self, word: str, translation: str) -> bool:
        """Проверяет перевод, который дал пользователь.

        Слово и перевод нормализуются, поэтому регистр и пробелы
        по краям не важны.

        Args:
            word: Слово, которое переводил пользователь.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если перевод правильный, иначе False.

        Raises:
            ValueError: Если word или translation не строка
                или слова нет в игре.
        """
        return self.get_translation(word) == self.normalize_word(translation)
