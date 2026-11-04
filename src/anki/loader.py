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
