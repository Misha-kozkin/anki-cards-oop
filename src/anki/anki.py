from typing import Optional


class Anki:
    """Основная логика игры: хранение и угадывание слов."""

    def __init__(self, *, words: Optional[dict[str, str]] = None) -> None:
        if words is None:
            words = {}
        if not isinstance(words, dict):
            raise ValueError('Параметр words должен быть словарём')
        self._words: dict[str, str] = {}
        for word, translation in words.items():
            self.add_word(word, translation)

    @staticmethod
    def normalize_word(word: str) -> str:
        """Убирает пробелы по краям и приводит слово к нижнему регистру."""
        if not isinstance(word, str):
            raise ValueError(
                f'Слово должно быть строкой, получено: {type(word).__name__}'
            )
        return word.strip().lower()

    def add_word(self, word: str, translation: str) -> None:
        """Добавляет в словарь пару «слово - перевод» после нормализации."""
        normalized_word = self.normalize_word(word)
        normalized_translation = self.normalize_word(translation)
        self._words[normalized_word] = normalized_translation

    def get_words(self) -> dict[str, str]:
        """Возвращает копию словаря со словами."""
        return self._words.copy()
