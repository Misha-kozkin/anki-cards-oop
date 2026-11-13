"""Тесты выбора загрузчика и сетевого загрузчика."""

from typing import Any

import pytest
import requests

from anki import main
from anki.loader import (
    JsonFileLoader,
    JsonNetworkLoader,
    LoaderRegistry,
    TextFileLoader,
    TSVFileLoader,
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


def test_new_format_works_without_changing_get_loader(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Новый формат подключается одним декоратором, get_loader не меняется."""
    registry = LoaderRegistry()

    @registry.register('.csv')
    class CsvLoader:
        """Подделка загрузчика CSV для теста."""

        def __init__(self, *, file_path: str) -> None:
            """Запоминает путь к файлу."""
            self.file_path = file_path

    monkeypatch.setattr(main, 'loader_registry', registry)
    loader = get_loader('words.CSV')
    assert isinstance(loader, CsvLoader)
    assert loader.file_path == 'words.CSV'


def test_register_returns_class_unchanged() -> None:
    """Декоратор register возвращает тот же класс, а не обёртку."""
    registry = LoaderRegistry()

    class Original:
        """Класс для проверки."""

    assert registry.register('.x')(Original) is Original
