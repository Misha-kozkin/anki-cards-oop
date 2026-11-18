"""Основная логика игры Anki: слова, проверка переводов, тренировка."""

import random
import time
from collections.abc import Iterator
from typing import Optional, Union


class Anki:
    """Хранит словарь игры и следит за единым форматом слов.

    Инвариант класса: все слова и переводы в словаре нормализованы,
    то есть без пробелов по краям и в нижнем регистре. Все способы
    изменить слова (инициализатор, свойство words, add_word)
    проходят через нормализацию.

    Класс также ведёт тренировку до первой ошибки: считает
    правильные ответы и время и не даёт «накрутить» счёт.

    Attributes:
        last_session_stats: Итоги последней тренировки: количество
            правильных ответов (correct_answers) и время в секундах
            (total_time).
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
        self._session_active: bool = False
        self._session_start_time: float = 0.0
        self._session_user_score: int = 0
        self._last_word: Optional[str] = None
        self.last_session_stats: dict[str, Union[int, float]] = {
            'correct_answers': 0,
            'total_time': 0.0,
        }
        self._words: dict[str, str] = {}
        self.words = words if words is not None else {}

    @staticmethod
    def normalize_word(word: str) -> str:
        """Приводит слово к внутреннему формату игры.

        Убирает пробельные символы по краям и переводит все
        буквы в нижний регистр.

        Args:
            word: Слово или перевод для нормализации.

        Returns:
            Нормализованная строка.

        Raises:
            ValueError: Если word не является строкой.

        Examples:
            >>> Anki.normalize_word('  PyThOn  ')
            'python'
        """
        if not isinstance(word, str):
            raise ValueError(
                f'Слово должно быть строкой, получено: {type(word).__name__}'
            )
        return word.strip().lower()

    def _normalize_dict(self, words: dict[str, str]) -> dict[str, str]:
        """Возвращает новый словарь с нормализованными словами.

        Args:
            words: Словарь {слово: перевод}.

        Returns:
            Новый словарь, где ключи и значения нормализованы.

        Raises:
            ValueError: Если words не словарь или в нём есть
                ключи или значения, которые не являются строками.
        """
        if not isinstance(words, dict):
            raise ValueError('Слова должны быть словарём')
        return {
            self.normalize_word(word): self.normalize_word(translation)
            for word, translation in words.items()
        }

    @property
    def words(self) -> dict[str, str]:
        """Копия словаря {слово: перевод}.

        Изменение полученного словаря не влияет на игру. Чтобы
        заменить все слова, присвойте свойству новый словарь.
        Чтобы добавить одно слово, используйте add_word.
        """
        return self._words.copy()

    @words.setter
    def words(self, value: dict[str, str]) -> None:
        """Заменяет все слова игры новыми после нормализации.

        Args:
            value: Новый словарь {слово: перевод}.

        Raises:
            ValueError: Если идёт тренировка, если value не словарь
                или в нём есть ключи или значения не строки.
        """
        if self._session_active:
            raise ValueError('Нельзя заменить все слова во время тренировки')
        self._words = self._normalize_dict(value)

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

    def __iter__(self) -> Iterator[tuple[str, str]]:
        """Позволяет перебирать игру в цикле for.

        Returns:
            Итератор по парам (слово, перевод).

        Examples:
            >>> for word, translation in Anki(words={'cat': 'кот'}):
            ...     print(word, '-', translation)
            cat - кот
        """
        return iter(self._words.items())

    def __len__(self) -> int:
        """Возвращает количество слов в игре для len().

        Returns:
            Число пар «слово - перевод».

        Examples:
            >>> len(Anki(words={'cat': 'кот', 'dog': 'собака'}))
            2
        """
        return len(self._words)

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
        """Выбирает случайное слово из игры и запоминает его.

        Во время тренировки проверить перевод можно только
        у последнего выданного слова.

        Returns:
            Случайное слово (без перевода).

        Raises:
            ValueError: Если в игре нет ни одного слова.
        """
        if not self._words:
            raise ValueError('В игре нет слов. Сначала добавьте слова.')
        word = random.choice(list(self._words))
        self._last_word = word
        return word

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
        по краям не важны. Во время тренировки правильный ответ
        добавляет очко, а неправильный завершает тренировку.

        Args:
            word: Слово, которое переводил пользователь.
            translation: Перевод, который ввёл пользователь.

        Returns:
            True, если перевод правильный, иначе False.

        Raises:
            ValueError: Если word или translation не строка, слова
                нет в игре или, во время тренировки, word не последнее
                выданное слово (тогда тренировка завершается).
        """
        if self._session_active:
            if self.normalize_word(word) != self._last_word:
                self.end_session()
                raise ValueError(
                    'Проверить можно только последнее выданное слово'
                )
            self._last_word = None
        is_correct = (
            self.get_translation(word) == self.normalize_word(translation)
        )
        if self._session_active:
            if is_correct:
                self._session_user_score += 1
            else:
                self.end_session()
        return is_correct

    def start_session(self) -> None:
        """Начинает тренировку до первой ошибки.

        Raises:
            RuntimeError: Если тренировка уже идёт.
        """
        if self._session_active:
            raise RuntimeError('Тренировка уже идёт')
        self._session_active = True
        self._session_start_time = time.time()
        self._session_user_score = 0
        self._last_word = None

    def end_session(self) -> None:
        """Завершает тренировку и сохраняет её итоги в last_session_stats.

        Raises:
            RuntimeError: Если тренировка не идёт.
        """
        if not self._session_active:
            raise RuntimeError('Нельзя завершить тренировку, она не идёт')
        self.last_session_stats = {
            'correct_answers': self._session_user_score,
            'total_time': time.time() - self._session_start_time,
        }
        self._session_active = False
        self._session_start_time = 0.0
        self._session_user_score = 0
        self._last_word = None
