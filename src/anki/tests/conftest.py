"""Общие фикстуры для тестов пакета anki."""

from pathlib import Path

import pytest


@pytest.fixture()
def words_file(tmp_path: Path) -> Path:
    """Создаёт временный файл с двумя парами слов.

    Args:
        tmp_path: Встроенная фикстура pytest с временной директорией.

    Returns:
        Путь к созданному файлу.
    """
    path = tmp_path / 'test_words.txt'
    path.write_text('hello,привет\nworld,мир\n', encoding='utf-8')
    return path


@pytest.fixture()
def empty_file(tmp_path: Path) -> Path:
    """Возвращает путь к файлу, которого ещё не существует.

    Args:
        tmp_path: Встроенная фикстура pytest с временной директорией.

    Returns:
        Путь к несуществующему файлу во временной директории.
    """
    return tmp_path / 'new_words.txt'
