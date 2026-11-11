"""Загрузчики слов игры Anki: текстовый, TSV и JSON форматы."""

import json
from pathlib import Path
from typing import ClassVar, Optional, TextIO, Union

import requests


class BaseFileLoader:
    """Общая логика загрузки и сохранения слов в файле.

    Базовый класс открывает и закрывает файл, проверяет путь
    и аргументы. Как именно слова записаны внутри файла, решают
    наследники: они переопределяют методы _load_from_file
    и _save_to_file.

    Attributes:
        DEFAULT_FILE_PATH: Путь к файлу, если он не передан
            при создании загрузчика.
    """

    DEFAULT_FILE_PATH: ClassVar[str] = './words.txt'

    def __init__(
        self, *, file_path: Optional[Union[str, Path]] = None
    ) -> None:
        """Запоминает путь к файлу со словами.

        Args:
            file_path: Путь к файлу. Если не передан, используется
                DEFAULT_FILE_PATH класса. Файл может ещё не
                существовать, он будет создан при сохранении.

        Raises:
            ValueError: Если file_path указывает на директорию.
        """
        if file_path is None:
            file_path = self.DEFAULT_FILE_PATH
        path = Path(file_path)
        if path.is_dir():
            raise ValueError(
                f'Путь {path} указывает на директорию, а нужен файл'
            )
        self._file_path: Path = path

    def load_words(self) -> dict[str, str]:
        """Читает слова из файла.

        Returns:
            Словарь {слово: перевод}. Если файла нет,
            возвращается пустой словарь.
        """
        try:
            with self._file_path.open(encoding='utf-8') as file:
                return self._load_from_file(file)
        except FileNotFoundError:
            return {}

    def save_words(self, words: dict[str, str]) -> None:
        """Перезаписывает файл словами из словаря.

        Старое содержимое файла удаляется. Если файла нет,
        он создаётся.

        Args:
            words: Словарь {слово: перевод} для сохранения.

        Raises:
            ValueError: Если words не является словарём.
        """
        if not isinstance(words, dict):
            raise ValueError('Параметр words должен быть словарём')
        with self._file_path.open('w', encoding='utf-8') as file:
            self._save_to_file(words, file)

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Читает слова из открытого файла в формате наследника.

        Args:
            file_object: Файл, открытый на чтение.

        Returns:
            Словарь {слово: перевод}.

        Raises:
            NotImplementedError: Если наследник не переопределил метод.
        """
        raise NotImplementedError

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        """Записывает слова в открытый файл в формате наследника.

        Args:
            words: Словарь {слово: перевод}.
            file_object: Файл, открытый на запись.

        Raises:
            NotImplementedError: Если наследник не переопределил метод.
        """
        raise NotImplementedError


class TextFileLoader(BaseFileLoader):
    """Хранит слова в текстовом файле, по паре на строку.

    Формат строки: «слово,перевод». Строки без запятой или
    с несколькими запятыми при загрузке пропускаются.
    """

    DEFAULT_FILE_PATH: ClassVar[str] = './words.txt'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Читает строки «слово,перевод», пропуская неверные."""
        words: dict[str, str] = {}
        for line in file_object:
            parts = line.strip().split(',')
            if len(parts) == 2:
                word, translation = parts
                words[word] = translation
        return words

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        """Записывает каждую пару строкой «слово,перевод»."""
        for word, translation in words.items():
            file_object.write(word + ',' + translation + '\n')


class TSVFileLoader(BaseFileLoader):
    """Хранит слова в TSV-файле: слово и перевод разделены табуляцией.

    Строки без табуляции или с несколькими табуляциями
    при загрузке пропускаются.
    """

    DEFAULT_FILE_PATH: ClassVar[str] = './words.tsv'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Читает строки «слово<TAB>перевод», пропуская неверные."""
        words: dict[str, str] = {}
        for line in file_object:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                word, translation = parts
                words[word] = translation
        return words

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        """Записывает каждую пару строкой «слово<TAB>перевод»."""
        for word, translation in words.items():
            file_object.write(f'{word}\t{translation}\n')


class JsonFileLoader(BaseFileLoader):
    """Хранит слова в JSON-файле как один объект {слово: перевод}."""

    DEFAULT_FILE_PATH: ClassVar[str] = './words.json'

    def _load_from_file(self, file_object: TextIO) -> dict[str, str]:
        """Читает JSON-объект со словами.

        Args:
            file_object: Файл, открытый на чтение.

        Returns:
            Словарь {слово: перевод}.

        Raises:
            ValueError: Если в файле некорректный JSON или не объект.
        """
        data = json.load(file_object)
        if not isinstance(data, dict):
            raise ValueError(
                'В JSON-файле должен быть объект {слово: перевод}'
            )
        return data

    def _save_to_file(
        self, words: dict[str, str], file_object: TextIO
    ) -> None:
        """Записывает слова как JSON с отступом 2 и кириллицей как есть."""
        json.dump(words, file_object, indent=2, ensure_ascii=False)


class JsonNetworkLoader:
    """Загружает слова из JSON-объекта по HTTP-ссылке.

    Не наследуется от BaseFileLoader, но имеет те же методы
    load_words и save_words, поэтому игра может использовать
    его вместо файлового загрузчика.

    Attributes:
        url: Адрес, по которому лежит JSON со словами.
    """

    def __init__(self, url: str) -> None:
        """Запоминает адрес источника слов.

        Args:
            url: Ссылка на JSON-объект {слово: перевод}.
        """
        self.url = url

    def load_words(self) -> dict[str, str]:
        """Скачивает слова по ссылке из атрибута url.

        Returns:
            Словарь {слово: перевод}.

        Raises:
            requests.RequestException: Если сервер недоступен
                или ответил ошибкой.
            ValueError: Если в ответе не JSON-объект.
        """
        response = requests.get(self.url)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            raise ValueError(
                'По ссылке должен быть JSON-объект {слово: перевод}'
            )
        return data

    def save_words(self, words: dict[str, str]) -> None:
        """Ничего не делает: сохранять слова по ссылке нельзя.

        Args:
            words: Словарь {слово: перевод}. Не используется.
        """
