"""Точка входа игры Anki: выбирает загрузчик и запускает интерфейс."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Union

import requests

from anki.anki import Anki
from anki.loader import BaseFileLoader, JsonNetworkLoader, loader_registry
from anki.ui import TextUI
from types import TracebackType

WORDS_FILE: Path = Path(__file__).parent / 'words.txt'

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


class WordsLoadError(Exception):
    """Не удалось загрузить слова из источника."""


class GameContext:
    """Контекстный менеджер жизненного цикла игры.

    При входе в блок with загружает слова в игру, при выходе
    сохраняет их через загрузчик. Сохранение выполняется,
    даже если внутри блока произошла ошибка.

    Examples:
        with GameContext(loader, anki):
            TextUI(anki).main_loop()
    """

    def __init__(self, loader: Loader, anki: Anki) -> None:
        """Запоминает загрузчик и игру.

        Args:
            loader: Загрузчик с методами load_words и save_words.
            anki: Игра, в которую загружаются слова.
        """
        self._loader: Loader = loader
        self._anki: Anki = anki

    def __enter__(self) -> Anki:
        """Загружает слова в игру.

        Returns:
            Игру с загруженными словами (для with ... as ...).

        Raises:
            WordsLoadError: Если слова не удалось загрузить.
        """
        try:
            self._anki.words = self._loader.load_words()
        except (requests.RequestException, ValueError) as error:
            raise WordsLoadError(str(error)) from error
        return self._anki

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Сохраняет слова игры при любом выходе из блока with.

        Исключение из блока не подавляется: метод возвращает None,
        и Python пробрасывает ошибку дальше после сохранения.

        Args:
            exc_type: Тип исключения или None, если ошибки не было.
            exc_value: Само исключение или None.
            traceback: Трассировка исключения или None.
        """
        self._loader.save_words(self._anki.words)


def main() -> None:
    """Разбирает аргументы и запускает игру в контексте GameContext."""
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

    anki = Anki()
    try:
        with GameContext(loader, anki):
            ui = TextUI(anki)
            ui.main_loop()
    except WordsLoadError as error:
        sys.exit(f'Не удалось загрузить слова: {error}')


if __name__ == '__main__':
    main()
