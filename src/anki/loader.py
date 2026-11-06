from pathlib import Path
from typing import Union


class TextFileLoader:
    """Загрузка слов из текстового файла."""

    def __init__(
        self, *, file_path: Union[str, Path] = './words.txt'
    ) -> None:
        path = Path(file_path)
        if path.is_dir():
            raise ValueError(
                f'Путь {path} указывает на директорию, а нужен файл'
            )
        self.file_path: Path = path

    def load_words(self) -> dict[str, str]:
        """Читает пары «слово,перевод» из файла.

        Строки без запятой или с лишними запятыми пропускаются.
        Если файла нет, возвращает пустой словарь.
        """
        words: dict[str, str] = {}
        try:
            with self.file_path.open(encoding='utf-8') as file:
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) == 2:
                        word, translation = parts
                        words[word] = translation
        except FileNotFoundError:
            return {}
        return words

    def save_words(self, words: dict[str, str]) -> None:
        """Перезаписывает файл парами «слово,перевод» из словаря."""
        if not isinstance(words, dict):
            raise ValueError('Параметр words должен быть словарём')
        with self.file_path.open('w', encoding='utf-8') as file:
            for word, translation in words.items():
                file.write(word + ',' + translation + '\n')
