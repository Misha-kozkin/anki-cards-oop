"""Точка входа игры Anki: связывает загрузчик, игру и интерфейс."""

from pathlib import Path

from anki.anki import Anki
from anki.loader import TextFileLoader
from anki.ui import TextUI

WORDS_FILE = Path(__file__).parent / 'words.txt'


def main() -> None:
    """Загружает слова, запускает меню и сохраняет слова при выходе."""
    loader = TextFileLoader(file_path=WORDS_FILE)

    anki = Anki(words=loader.load_words())

    ui = TextUI(anki)
    ui.main_loop()

    loader.save_words(anki.get_words())


if __name__ == '__main__':
    main()
