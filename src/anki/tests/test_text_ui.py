"""Тесты класса TextUI с подменой ввода."""

from collections.abc import Iterator

import pytest

from anki.anki import Anki
from anki.ui import TextUI


def fake_input(answers: list[str]) -> Iterator[str]:
    """Превращает список ответов в итератор для подмены input()."""
    return iter(answers)


def test_show_words_prints_each_pair_on_own_line(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Метод show_words печатает количество слов и пары по строке."""
    ui = TextUI(Anki(words={'cat': 'кот', 'dog': 'собака'}))
    ui.show_words()
    lines = capsys.readouterr().out.splitlines()
    assert lines == ['Всего слов: 2', 'cat - кот', 'dog - собака']


def test_add_words_adds_valid_pairs_and_skips_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Метод add_words добавляет пары и пропускает пустые и с запятой."""
    anki = Anki()
    answers = fake_input(['Cat', ' Кот ', 'а,б', 'в', '', 'x', 'стоп'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(anki).add_words()
    assert anki.words == {'cat': 'кот'}


def test_start_game_reports_empty_game(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Метод start_game не падает, если в игре нет слов."""
    TextUI(Anki()).start_game()
    assert 'нет слов' in capsys.readouterr().out


def test_main_loop_stops_on_exit_and_reports_unknown_choice(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Метод main_loop сообщает о неизвестном пункте и выходит по «Выход».

    В пустой игре в меню два пункта, поэтому «Выход» — это «2».
    """
    answers = fake_input(['abc', '5', '2'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(Anki()).main_loop()
    assert capsys.readouterr().out.count('Неизвестный пункт меню') == 2


def test_train_until_mistake_counts_answers_until_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Тренировка идёт до первой ошибки и показывает итоги."""
    anki = Anki(words={'cat': 'кот'})
    answers = fake_input(['кот', 'Кот ', 'dog'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(anki).train_until_mistake()
    output = capsys.readouterr().out
    assert 'Правильных ответов: 2' in output
    assert 'Правильный ответ: кот' in output


def test_train_until_mistake_stop_word_ends_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """После выхода по STOP_WORD можно начать новую тренировку."""
    anki = Anki(words={'cat': 'кот'})
    answers = fake_input(['стоп'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(anki).train_until_mistake()
    anki.start_session()


def test_train_until_mistake_with_empty_game(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Пустая игра не ломает тренировку и не оставляет её активной."""
    anki = Anki()
    TextUI(anki).train_until_mistake()
    assert 'нет слов' in capsys.readouterr().out
    anki.start_session()


def test_menu_of_empty_game_has_only_add_words_and_exit() -> None:
    """Без слов в меню остаются только «Добавить слова» и «Выход»."""
    ui = TextUI(Anki())
    descriptions = [desc for _, desc in ui.get_available_commands()]
    assert descriptions == ['Добавить слова', 'Выход']


def test_menu_with_words_shows_all_commands_in_order() -> None:
    """Со словами меню показывает все пункты в порядке объявления."""
    ui = TextUI(Anki(words={'cat': 'кот'}))
    descriptions = [desc for _, desc in ui.get_available_commands()]
    assert descriptions == [
        'Начать игру',
        'Добавить слова',
        'Тренировка до первой ошибки',
        'Найти перевод',
        'Вывод всех слов',
        'Выход',
    ]


def test_menu_appears_after_adding_first_word(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """После добавления слова меню перестраивается и нумерация меняется."""
    answers = fake_input(['1', 'cat', 'кот', 'стоп', '6'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(Anki()).main_loop()
    output = capsys.readouterr().out
    assert '2. Выход' in output
    assert '6. Выход' in output


def test_stop_sets_is_running_to_false() -> None:
    """Метод stop останавливает главный цикл."""
    ui = TextUI(Anki())
    ui._is_running = True
    ui.stop()
    assert ui._is_running is False


@pytest.mark.parametrize('word', ['cat', '  CAT '])
def test_find_translation_prints_translation(
    word: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Метод find_translation находит слово без учёта регистра и пробелов."""
    answers = fake_input([word])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(Anki(words={'cat': 'кот'})).find_translation()
    assert 'Перевод: кот' in capsys.readouterr().out


def test_find_translation_reports_missing_word(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
) -> None:
    """Метод find_translation сообщает, что слова нет, и не падает."""
    answers = fake_input(['dog'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(Anki(words={'cat': 'кот'})).find_translation()
    output = capsys.readouterr().out
    assert 'нет в игре' in output
    assert 'кот' not in output
