"""Тесты класса TextFileLoader."""

from pathlib import Path

from anki.loader import TextFileLoader


def test_load_words_loads_words_from_comma_separated_values(
    words_file: Path,
) -> None:
    """Метод load_words читает пары «слово,перевод» из файла."""
    loader = TextFileLoader(file_path=words_file)
    assert loader.load_words() == {'hello': 'привет', 'world': 'мир'}


def test_load_words_returns_empty_dict_for_missing_file(
    empty_file: Path,
) -> None:
    """Метод load_words возвращает пустой словарь, если файла нет."""
    loader = TextFileLoader(file_path=empty_file)
    assert loader.load_words() == {}


def test_save_words_saves_words_as_comma_separated_values(
    empty_file: Path,
) -> None:
    """Метод save_words пишет каждую пару в формате «слово,перевод»."""
    loader = TextFileLoader(file_path=empty_file)
    loader.save_words({'python': 'питон', 'code': 'код'})
    content = empty_file.read_text(encoding='utf-8')
    assert content == 'python,питон\ncode,код\n', (
        'Каждая пара должна быть записана в отдельной строке'
        ' в формате «слово,перевод»'
    )


def test_save_words_overwrites_file(words_file: Path) -> None:
    """Метод save_words заменяет старое содержимое файла."""
    loader = TextFileLoader(file_path=words_file)
    loader.save_words({'new': 'новый'})
    assert words_file.read_text(encoding='utf-8') == 'new,новый\n'
