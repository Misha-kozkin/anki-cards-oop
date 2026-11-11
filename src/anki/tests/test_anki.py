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


@pytest.mark.parametrize('word', ['hello', 'HELLO', '  Hello  ', '\thello\n'])
def test_contains_finds_word_regardless_of_case_and_spaces(word: str) -> None:
    """Оператор in находит слово независимо от регистра и пробелов."""
    anki = Anki(words={'hello': 'привет'})
    assert word in anki, (
        f'Слово {word!r} должно находиться в колоде после нормализации'
    )


def test_contains_returns_false_for_missing_word() -> None:
    """Оператор in возвращает False для слова, которого нет в колоде."""
    anki = Anki(words={'hello': 'привет'})
    assert 'python' not in anki


def test_contains_searches_words_not_translations() -> None:
    """Оператор in ищет среди слов, а не среди переводов."""
    anki = Anki(words={'hello': 'привет'})
    assert 'привет' not in anki


@pytest.mark.parametrize('invalid_input', [1, None, [], set()])
def test_contains_raises_ValueError_on_invalid_input(
    invalid_input: Any,
) -> None:
    """Оператор in выбрасывает ValueError, если искомое — не строка."""
    anki = Anki()
    with pytest.raises(ValueError, match='должно быть строкой'):
        invalid_input in anki
        pytest.fail('Оператор in должен выдавать ValueError для не-строки')


@pytest.mark.parametrize(
    'words, expected', [
        ({}, 'Колода Anki, слов в колоде: 0'),
        ({'cat': 'кот'}, 'Колода Anki, слов в колоде: 1'),
        ({'cat': 'кот', 'dog': 'собака'}, 'Колода Anki, слов в колоде: 2'),
    ]
)
def test_str_shows_number_of_words(
    words: dict[str, str], expected: str
) -> None:
    """Функция str() показывает количество слов в колоде."""
    assert str(Anki(words=words)) == expected


@pytest.fixture()
def anki_with_words() -> Anki:
    """Возвращает игру с двумя словами."""
    return Anki(words={'hello': 'привет', 'world': 'мир'})


def test_get_random_word_raises_ValueError_for_empty_game() -> None:
    """Метод get_random_word выбрасывает ValueError, если слов нет."""
    with pytest.raises(ValueError, match='нет слов'):
        Anki().get_random_word()
        pytest.fail('Для пустой игры должна быть ошибка ValueError')


def test_get_random_word_returns_word_from_game(anki_with_words: Anki) -> None:
    """Метод get_random_word возвращает слово, а не перевод."""
    for _ in range(20):
        assert anki_with_words.get_random_word() in {'hello', 'world'}


@pytest.mark.parametrize(
    'word, expected', [('hello', 'привет'), ('  WORLD ', 'мир')]
)
def test_get_translation_returns_translation(
    anki_with_words: Anki, word: str, expected: str
) -> None:
    """Метод get_translation находит перевод нормализованного слова."""
    assert anki_with_words.get_translation(word) == expected


def test_get_translation_raises_ValueError_for_missing_word(
    anki_with_words: Anki,
) -> None:
    """Метод get_translation выбрасывает ValueError для чужого слова."""
    with pytest.raises(ValueError, match='python'):
        anki_with_words.get_translation('PYTHON')
        pytest.fail('Для отсутствующего слова должна быть ошибка ValueError')


@pytest.mark.parametrize(
    'word, translation, expected', [
        ('hello', 'привет', True),
        (' HELLO ', '  ПРИВЕТ ', True),
        ('hello', 'мир', False),
        ('world', '', False),
    ]
)
def test_check_translation(
    anki_with_words: Anki, word: str, translation: str, expected: bool
) -> None:
    """Метод check_translation сравнивает нормализованные значения."""
    assert anki_with_words.check_translation(word, translation) is expected


def test_check_translation_raises_ValueError_for_missing_word(
    anki_with_words: Anki,
) -> None:
    """Метод check_translation выбрасывает ValueError для чужого слова."""
    with pytest.raises(ValueError):
        anki_with_words.check_translation('python', 'питон')
        pytest.fail('Для отсутствующего слова должна быть ошибка ValueError')


def test_anki_iterates_over_word_translation_pairs(
    anki_with_words: Anki,
) -> None:
    """Цикл for по игре выдаёт пары (слово, перевод)."""
    assert list(anki_with_words) == [('hello', 'привет'), ('world', 'мир')]


@pytest.mark.parametrize(
    'words, expected', [
        ({}, 0),
        ({'cat': 'кот'}, 1),
        ({'Cat': 'кот', 'cat': 'кошка'}, 1),
    ],
    ids=['empty', 'one', 'duplicates_after_normalization'],
)
def test_len_returns_number_of_words(
    words: dict[str, str], expected: int
) -> None:
    """Функция len() возвращает число уникальных нормализованных слов."""
    assert len(Anki(words=words)) == expected


def test_empty_anki_is_falsy() -> None:
    """Пустая игра считается ложной в if благодаря __len__."""
    assert not Anki()
    assert Anki(words={'cat': 'кот'})
