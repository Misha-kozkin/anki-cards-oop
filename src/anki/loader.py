"""Загрузчики слов игры Anki: текстовый, TSV и JSON форматы."""

import json
from pathlib import Path
from typing import Callable, ClassVar, Optional, Protocol, Self, TextIO, Union

import requests


class LoaderProtocol(Protocol):
    """Любой загрузчик слов: важны методы, а не родительский класс."""

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт загрузчик по строке источника."""
        ...

    def load_words(self) -> dict[str, str]:
        """Загружает слова."""
        ...

    def save_words(self, words: dict[str, str]) -> None:
        """Сохраняет слова."""
        ...


class LoaderRegistry:
    """Реестр загрузчиков: связывает класс со стратегией выбора.

    Стратегия — функция, которая по строке источника отвечает,
    подходит ли загрузчик. Новый загрузчик регистрируется
    декоратором register, код выбора загрузчика не меняется.

    Examples:
        >>> registry = LoaderRegistry()
        >>> @registry.register(lambda source: source.endswith('.csv'))
        ... class CsvLoader:
        ...     pass
        >>> registry.get_loader('words.csv') is CsvLoader
        True
    """

    def __init__(self) -> None:
        """Создаёт пустой реестр."""
        self._registry: dict[type[LoaderProtocol], Callable[[str], bool]] = {}

    def register(
        self, predicate: Callable[[str], bool]
    ) -> Callable[[type[LoaderProtocol]], type[LoaderProtocol]]:
        """Создаёт декоратор, который регистрирует класс загрузчика.

        Args:
            predicate: Стратегия: функция, которая получает строку
                источника и возвращает True, если загрузчик подходит.

        Returns:
            Декоратор. Он запоминает класс со стратегией в реестре
            и возвращает этот же класс без изменений.
        """
        def decorator(cls: type[LoaderProtocol]) -> type[LoaderProtocol]:
            self._registry[cls] = predicate
            return cls

        return decorator

    def get_loader(self, source: str) -> type[LoaderProtocol]:
        """Находит класс загрузчика, стратегия которого подходит к source.

        Стратегии проверяются в порядке регистрации, побеждает первая,
        вернувшая True.

        Args:
            source: Путь к файлу со словами или ссылка.

        Returns:
            Класс подходящего загрузчика.

        Raises:
            ValueError: Если ни одна стратегия не подошла.
        """
        for loader_cls, predicate in self._registry.items():
            if predicate(source):
                return loader_cls
        raise ValueError(f'Неизвестный тип источника слов: {source}')


loader_registry: LoaderRegistry = LoaderRegistry()


def is_url_source(source: str) -> bool:
    """Проверяет, что источник — ссылка http:// или https://.

    Args:
        source: Строка источника.

    Returns:
        True, если это ссылка.
    """
    return source.startswith(('http://', 'https://'))


def is_txt_source(source: str) -> bool:
    """Проверяет, что источник — локальный файл .txt.

    Args:
        source: Строка источника.

    Returns:
        True для файла с расширением .txt (без учёта регистра).
    """
    return not is_url_source(source) and Path(source).suffix.lower() == '.txt'


def is_tsv_source(source: str) -> bool:
    """Проверяет, что источник — локальный файл .tsv.

    Args:
        source: Строка источника.

    Returns:
        True для файла с расширением .tsv (без учёта регистра).
    """
    return not is_url_source(source) and Path(source).suffix.lower() == '.tsv'


def is_json_source(source: str) -> bool:
    """Проверяет, что источник — локальный файл .json.

    Args:
        source: Строка источника.

    Returns:
        True для файла с расширением .json (без учёта регистра).
    """
    return (
        not is_url_source(source) and Path(source).suffix.lower() == '.json'
    )


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

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт загрузчик для файла по пути из source.

        Args:
            source: Путь к файлу со словами.

        Returns:
            Загрузчик того класса, у которого вызван метод.
        """
        return cls(file_path=source)

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


@loader_registry.register(is_txt_source)
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


@loader_registry.register(is_tsv_source)
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


@loader_registry.register(is_json_source)
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


@loader_registry.register(is_url_source)
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
        self.url: str = url

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт загрузчик для ссылки из source.

        Args:
            source: Ссылка на JSON со словами.

        Returns:
            Сетевой загрузчик.
        """
        return cls(url=source)

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
