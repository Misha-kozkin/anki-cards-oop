"""Тесты класса Anki."""

from typing import Any

import pytest

from anki.anki import Anki


@pytest.mark.parametrize(
    'word, case, expected', [
        ('hello', 'корректных данных', 'hello'),
        (
            'hello world',
            'отсутствия пробельных символов в начале или конце строки',
            'hello world',
        ),
    ]
)
def test_normalize_word_method_returns_valid_input_unchanged(
    word: str, case: str, expected: str
) -> None:
    """Метод normalize_word не меняет уже нормализованную строку."""
    assert Anki.normalize_word(word) == expected, (
        'Метод `normalize_word` должен возвращать неизменённую строку,'
        f' в случае {case}'
    )


@pytest.mark.parametrize(
    'word, expected', [
        ('pYtHoN', 'python'),
        ('Hello World', 'hello world'),
        ('   Python   ', 'python'),
        ('\tHello World\n', 'hello world'),
    ]
)
def test_normalize_word_method_normalizes_word(
    word: str, expected: str
) -> None:
    """Метод normalize_word убирает пробелы по краям и понижает регистр."""
    assert Anki.normalize_word(word) == expected, (
        'Метод `normalize_word` должен нормализовать'
        ' некорректно отформатированные строки.'
    )


@pytest.mark.parametrize('invalid_input', [1, None, [], set()])
def test_normalize_word_raises_ValueError_on_invalid_input(
    invalid_input: Any,
) -> None:
    """Метод normalize_word выбрасывает ValueError для не-строки."""
    with pytest.raises(ValueError, match='должно быть строкой'):
        Anki.normalize_word(invalid_input)
        pytest.fail(
            'Метод `normalize_word` должен выдавать ValueError'
            ' для нестроковых параметров'
        )


@pytest.mark.parametrize('invalid_words', [[], 'кот,cat', 42, ('a', 'b')])
def test_anki_init_raises_ValueError_on_invalid_input(
    invalid_words: Any,
) -> None:
    """Инициализатор Anki выбрасывает ValueError, если words не словарь."""
    with pytest.raises(ValueError):
        Anki(words=invalid_words)
        pytest.fail(
            'Инициализатор `Anki` должен выдавать ValueError,'
            ' если в words передан не словарь'
        )


@pytest.mark.parametrize(
    'invalid_words', [{1: 'python'}, {'python': 1}, {None: None}]
)
def test_anki_init_raises_ValueError_on_non_string_items(
    invalid_words: Any,
) -> None:
    """Инициализатор Anki выбрасывает ValueError для не-строк в словаре."""
    with pytest.raises(ValueError):
        Anki(words=invalid_words)
        pytest.fail(
            'Инициализатор `Anki` должен выдавать ValueError,'
            ' если ключи или значения words не строки'
        )


@pytest.mark.parametrize(
    'word, translation', [
        (123, 'перевод'),
        ('слово', 456),
        (None, 'перевод'),
        ('слово', ['перевод']),
    ]
)
def test_anki_add_word_raises_ValueError_on_invalid_input(
    word: Any, translation: Any
) -> None:
    """Метод add_word выбрасывает ValueError, если слово или перевод не строка.

    После ошибки словарь не должен измениться.
    """
    anki = Anki()
    with pytest.raises(ValueError):
        anki.add_word(word, translation)
        pytest.fail(
            'Метод `add_word` должен выдавать ValueError,'
            ' если word или translation не строка'
        )
    assert anki.get_words() == {}, (
        'После ошибки в `add_word` словарь не должен меняться'
    )
