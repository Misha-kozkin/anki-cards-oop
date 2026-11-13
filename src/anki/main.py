"""Точка входа игры Anki: выбирает загрузчик и запускает интерфейс."""

import argparse
import sys
from pathlib import Path
from typing import Union

import requests

from anki.anki import Anki
from anki.loader import BaseFileLoader, JsonNetworkLoader, loader_registry
from anki.ui import TextUI

WORDS_FILE = Path(__file__).parent / 'words.txt'

Loader = Union[BaseFileLoader, JsonNetworkLoader]


def get_loader(source: str) -> Loader:
    """Создаёт загрузчик слов, подходящий для источника.

    Ссылка, начинающаяся с http:// или https://, ищется в реестре
    по идентификатору 'http'. Для файла идентификатор — его
    расширение, например '.txt'.

    Args:
        source: Путь к файлу со словами или ссылка на JSON.

    Returns:
        Загрузчик с методами load_words и save_words.

    Raises:
        ValueError: Если для источника нет зарегистрированного загрузчика.
    """
    if source.startswith(('http://', 'https://')):
        loader_cls = loader_registry.get_loader('http')
        return loader_cls(url=source)
    suffix = Path(source).suffix.lower()
    if suffix not in loader_registry:
        raise ValueError(f'Неизвестный тип источника слов: {source}')
    loader_cls = loader_registry.get_loader(suffix)
    return loader_cls(file_path=source)


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

    loader.save_words(anki.words)


if __name__ == '__main__':
    main()
