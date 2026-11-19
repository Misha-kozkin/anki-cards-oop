"""Тесты выбора загрузчика, стратегий и сетевого загрузчика."""

from typing import Any, Callable, Self

import pytest
import requests

from anki import main
from anki.loader import (
    JsonFileLoader,
    JsonNetworkLoader,
    LoaderRegistry,
    TextFileLoader,
    TSVFileLoader,
    is_json_source,
    is_tsv_source,
    is_txt_source,
    is_url_source,
)
from anki.main import get_loader


@pytest.mark.parametrize(
    'source, loader_cls', [
        ('words.txt', TextFileLoader),
        ('WORDS.TXT', TextFileLoader),
        ('data/words.tsv', TSVFileLoader),
        ('words.json', JsonFileLoader),
        ('http://example.com/words', JsonNetworkLoader),
        ('https://example.com/words.json', JsonNetworkLoader),
    ]
)
def test_get_loader_chooses_loader_by_source(
    source: str, loader_cls: type
) -> None:
    """Функция get_loader выбирает загрузчик по ссылке или расширению."""
    assert isinstance(get_loader(source), loader_cls)


@pytest.mark.parametrize('source', ['words.csv', 'words', 'httpwords.txt.bak'])
def test_get_loader_raises_ValueError_for_unknown_source(source: str) -> None:
    """Функция get_loader выбрасывает ValueError для неизвестного источника."""
    with pytest.raises(ValueError, match='Неизвестный тип'):
        get_loader(source)
        pytest.fail(f'Для {source!r} должна быть ошибка ValueError')


class FakeResponse:
    """Подделка ответа requests: отдаёт заранее заданный JSON."""

    def __init__(self, data: Any) -> None:
        """Запоминает данные, которые вернёт json()."""
        self._data = data

    def raise_for_status(self) -> None:
        """Притворяется успешным ответом сервера."""

    def json(self) -> Any:
        """Возвращает заданные данные."""
        return self._data


def test_network_loader_returns_words_from_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Сетевой загрузчик запрашивает url и возвращает словарь из ответа."""
    requested: list[str] = []

    def fake_get(url: str) -> FakeResponse:
        requested.append(url)
        return FakeResponse({'list': 'список'})

    monkeypatch.setattr(requests, 'get', fake_get)
    loader = JsonNetworkLoader('https://example.com/words')
    assert loader.load_words() == {'list': 'список'}
    assert requested == ['https://example.com/words']


def test_network_loader_rejects_non_object_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Сетевой загрузчик выбрасывает ValueError, если в ответе не объект."""
    monkeypatch.setattr(requests, 'get', lambda url: FakeResponse(['a', 'b']))
    with pytest.raises(ValueError):
        JsonNetworkLoader('https://example.com/words').load_words()
        pytest.fail('Для JSON-списка должна быть ошибка ValueError')


class CsvLoader:
    """Подделка загрузчика CSV: реализует LoaderProtocol без наследования."""

    def __init__(self, *, file_path: str) -> None:
        """Запоминает путь к файлу."""
        self.file_path = file_path

    @classmethod
    def from_source(cls, source: str) -> Self:
        """Создаёт подделку по строке источника."""
        return cls(file_path=source)

    def load_words(self) -> dict[str, str]:
        """Ничего не загружает."""
        return {}

    def save_words(self, words: dict[str, str]) -> None:
        """Ничего не сохраняет."""


def is_csv_source(source: str) -> bool:
    """Стратегия для тестового формата CSV."""
    return source.lower().endswith('.csv')


def test_new_format_works_without_changing_get_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Новый формат подключается одним декоратором, get_loader не меняется."""
    registry = LoaderRegistry()
    registry.register(is_csv_source)(CsvLoader)
    monkeypatch.setattr(main, 'loader_registry', registry)
    loader = get_loader('words.CSV')
    assert isinstance(loader, CsvLoader)
    assert loader.file_path == 'words.CSV'


def test_register_returns_class_unchanged() -> None:
    """Декоратор register возвращает тот же класс, а не обёртку."""
    registry = LoaderRegistry()
    assert registry.register(is_csv_source)(CsvLoader) is CsvLoader


def test_registry_uses_first_matching_strategy() -> None:
    """При нескольких подходящих стратегиях побеждает первая."""
    class SecondLoader(CsvLoader):
        """Ещё один загрузчик для того же формата."""

    registry = LoaderRegistry()
    registry.register(is_csv_source)(CsvLoader)
    registry.register(is_csv_source)(SecondLoader)
    assert registry.get_loader('words.csv') is CsvLoader


@pytest.mark.parametrize(
    'strategy, source, expected', [
        (is_txt_source, 'words.txt', True),
        (is_txt_source, 'data/WORDS.TXT', True),
        (is_txt_source, 'https://example.com/words.txt', False),
        (is_txt_source, 'words.tsv', False),
        (is_tsv_source, 'words.tsv', True),
        (is_tsv_source, 'words.txt', False),
        (is_json_source, 'words.json', True),
        (is_json_source, 'http://example.com/words.json', False),
        (is_url_source, 'https://example.com/words', True),
        (is_url_source, 'http://example.com/words.txt', True),
        (is_url_source, 'httpwords.txt', False),
    ]
)
def test_strategies(
    strategy: Callable[[str], bool], source: str, expected: bool
) -> None:
    """Каждая стратегия узнаёт свой источник и только его."""
    assert strategy(source) is expected


def test_url_ending_with_txt_goes_to_network_loader() -> None:
    """Ссылка на .txt — это сеть, а не локальный текстовый файл."""
    loader = get_loader('https://example.com/words.txt')
    assert isinstance(loader, JsonNetworkLoader)


def test_file_loaders_create_instance_of_own_class() -> None:
    """Метод from_source наследников возвращает объект своего класса."""
    assert type(TSVFileLoader.from_source('w.tsv')) is TSVFileLoader
    assert type(JsonFileLoader.from_source('w.json')) is JsonFileLoader
