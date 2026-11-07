"""Интеграционный тест: загрузка, работа с Anki и сохранение."""

from pathlib import Path

from anki.anki import Anki
from anki.loader import TextFileLoader


def test_integration(words_file: Path) -> None:
    """Слова проходят путь файл → Anki → файл без потерь."""
    loader = TextFileLoader(file_path=words_file)
    words = loader.load_words()

    anki = Anki(words=words)
    assert anki.get_words() == {'hello': 'привет', 'world': 'мир'}

    anki.add_word('  PyThOn ', ' Питон ')
    loader.save_words(anki.get_words())

    lines = words_file.read_text(encoding='utf-8').splitlines()
    assert sorted(lines) == ['hello,привет', 'python,питон', 'world,мир']
    assert TextFileLoader(file_path=words_file).load_words() == (
        anki.get_words()
    )
