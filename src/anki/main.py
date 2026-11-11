"""Точка входа игры Anki: выбирает загрузчик и запускает интерфейс."""

import argparse
import sys
from pathlib import Path
from typing import Union

import requests

from anki.anki import Anki
from anki.loader import (
    BaseFileLoader,
    JsonFileLoader,
    JsonNetworkLoader,
    TextFileLoader,
    TSVFileLoader,
)
from anki.ui import TextUI

WORDS_FILE = Path(__file__).parent / 'words.txt'

FILE_LOADERS: dict[str, type[BaseFileLoader]] = {
    '.txt': TextFileLoader,
    '.tsv': TSVFileLoader,
    '.json': JsonFileLoader,
}

Loader = Union[BaseFileLoader, JsonNetworkLoader]


def get_loader(source: str) -> Loader:
    """Выбирает загрузчик слов по источнику.

    Ссылка, начинающаяся с http:// или https://, загружается
    по сети. Для файла загрузчик выбирается по расширению.

    Args:
        source: Путь к файлу со словами или ссылка на JSON.

    Returns:
        Загрузчик с методами load_words и save_words.

    Raises:
        ValueError: Если тип источника неизвестен.
    """
    if source.startswith(('http://', 'https://')):
        return JsonNetworkLoader(source)
    path = Path(source)
    loader_cls = FILE_LOADERS.get(path.suffix.lower())
    if loader_cls is None:
        raise ValueError(f'Неизвестный тип источника слов: {source}')
    return loader_cls(file_path=path)


def main() -> None:
    """Разбирает аргументы, запускает игру и сохраняет слова при выходе."""
    parser = argparse.ArgumentParser(
        prog='anki', description='Тренажёр словарного запаса.'
    )
    parser.add_argument(
        '--source',
        default=str(WORDS_FILE),
        help=(
            'путь к файлу со словами (.txt, .tsv, .json) или ссылка '
            'http(s):// на JSON со словами; по умолчанию words.txt игры'
        ),
        metavar='SOURCE',
    )
    args = parser.parse_args()

    try:
        loader = get_loader(args.source)
    except ValueError as error:
        parser.error(str(error))

    try:
        words = loader.load_words()
    except (requests.RequestException, ValueError) as error:
        sys.exit(f'Не удалось загрузить слова: {error}')

    anki = Anki(words=words)

    ui = TextUI(anki)
    ui.main_loop()

    loader.save_words(anki.get_words())


if __name__ == '__main__':
    main()
