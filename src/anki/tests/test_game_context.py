"""Тесты контекстного менеджера GameContext."""

from pathlib import Path

import pytest

from anki.anki import Anki
from anki.loader import JsonFileLoader, TextFileLoader
from anki.main import GameContext, WordsLoadError


def test_game_context_loads_and_saves_words(words_file: Path) -> None:
    """При входе слова загружаются, при выходе — сохраняются."""
    loader = TextFileLoader(file_path=words_file)
    anki = Anki()
    with GameContext(loader, anki) as game:
        assert game is anki
        assert anki.words == {'hello': 'привет', 'world': 'мир'}
        anki.add_word('python', 'питон')
    assert loader.load_words()['python'] == 'питон'


def test_game_context_saves_words_on_error_and_reraises(
    words_file: Path,
) -> None:
    """Ошибка в блоке with не мешает сохранению и не подавляется."""
    loader = TextFileLoader(file_path=words_file)
    anki = Anki()
    with pytest.raises(RuntimeError, match='сбой'):
        with GameContext(loader, anki):
            anki.add_word('python', 'питон')
            raise RuntimeError('сбой')
    assert 'python' in loader.load_words()


def test_game_context_does_not_overwrite_file_if_load_failed(
    tmp_path: Path,
) -> None:
    """Если загрузка не удалась, файл со словами не перезаписывается."""
    broken = tmp_path / 'words.json'
    broken.write_text('{сломанный json', encoding='utf-8')
    with pytest.raises(WordsLoadError):
        with GameContext(JsonFileLoader(file_path=broken), Anki()):
            pytest.fail('Тело with не должно выполняться')
    assert broken.read_text(encoding='utf-8') == '{сломанный json'
