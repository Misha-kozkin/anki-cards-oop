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
    """Метод main_loop сообщает о неизвестном пункте и выходит по «5»."""
    answers = fake_input(['abc', '5'])
    monkeypatch.setattr('builtins.input', lambda prompt='': next(answers))
    TextUI(Anki()).main_loop()
    assert 'Неизвестный пункт меню' in capsys.readouterr().out


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
