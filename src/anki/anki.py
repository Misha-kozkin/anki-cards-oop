"""Основная логика игры Anki: хранение слов и их нормализация."""

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
