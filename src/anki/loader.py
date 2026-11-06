"""Загрузка и сохранение слов игры Anki в текстовом файле."""

from pathlib import Path
from typing import Union


class TextFileLoader:
    """Читает и записывает словарь игры в текстовый файл.

    Формат файла: одна пара на строку, слово и перевод разделены
    запятой без пробелов, например «кот,cat». Файл читается
    и записывается в кодировке UTF-8.
    """

    def __init__(
        self, *, file_path: Union[str, Path] = './words.txt'
    ) -> None:
        """Запоминает путь к файлу со словами.

        Args:
            file_path: Путь к файлу. Файл может ещё не существовать,
                он будет создан при сохранении.

        Raises:
            ValueError: Если file_path указывает на директорию.
        """
        path = Path(file_path)
        if path.is_dir():
            raise ValueError(
                f'Путь {path} указывает на директорию, а нужен файл'
            )
        self._file_path: Path = path

    def load_words(self) -> dict[str, str]:
        """Читает пары «слово,перевод» из файла.

        Строки без запятой или с лишними запятыми пропускаются.
        Слова возвращаются в том виде, в каком записаны в файле.

        Returns:
            Словарь {слово: перевод}. Если файла нет,
            возвращается пустой словарь.
        """
        words: dict[str, str] = {}
        try:
            with self._file_path.open(encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        word, translation = parts
                        words[word] = translation
        except FileNotFoundError:
            return {}
        return words

    def save_words(self, words: dict[str, str]) -> None:
        """Перезаписывает файл парами из словаря.

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
            for word, translation in words.items():
                file.write(word + ',' + translation + '\n')
