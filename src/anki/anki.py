from typing import Optional


class Anki:
    """Основная логика игры: хранение и угадывание слов."""

    def __init__(self, *, words: Optional[dict[str, str]] = None) -> None:
        if words is None:
            words = {}
        if not isinstance(words, dict):
            raise ValueError('Параметр words должен быть словарём')
        for word, translation in words.items():
            if not isinstance(word, str) or not isinstance(translation, str):
                raise ValueError(
                    'Все слова и переводы в words должны быть строками'
                )
        self.words: dict[str, str] = words
