"""Тесты загрузчиков слов."""

from pathlib import Path

import pytest

from anki.loader import (
    BaseFileLoader,
    JsonFileLoader,
    TextFileLoader,
    TSVFileLoader,
)


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


@pytest.mark.parametrize(
    'loader_cls', [TextFileLoader, TSVFileLoader, JsonFileLoader]
)
def test_loaders_save_and_load_same_words(
    loader_cls: type[BaseFileLoader], tmp_path: Path
) -> None:
    """Каждый загрузчик читает ровно то, что сам сохранил."""
    words = {'hello': 'привет', 'world': 'мир'}
    loader = loader_cls(file_path=tmp_path / 'words')
    loader.save_words(words)
    assert loader_cls(file_path=tmp_path / 'words').load_words() == words


@pytest.mark.parametrize(
    'loader_cls, expected_name', [
        (TextFileLoader, 'words.txt'),
        (TSVFileLoader, 'words.tsv'),
        (JsonFileLoader, 'words.json'),
    ]
)
def test_loaders_use_own_default_file_path(
    loader_cls: type[BaseFileLoader], expected_name: str
) -> None:
    """Без file_path каждый загрузчик берёт свой DEFAULT_FILE_PATH."""
    assert loader_cls()._file_path == Path(expected_name)


def test_json_loader_writes_cyrillic_with_indent(empty_file: Path) -> None:
    """Загрузчик JSON пишет кириллицу как есть и с отступом 2 пробела."""
    JsonFileLoader(file_path=empty_file).save_words({'cat': 'кот'})
    assert empty_file.read_text(encoding='utf-8') == '{\n  "cat": "кот"\n}'


def test_base_loader_requires_format_methods(words_file: Path) -> None:
    """Базовый загрузчик не знает формата и требует переопределения."""
    with pytest.raises(NotImplementedError):
        BaseFileLoader(file_path=words_file).load_words()
