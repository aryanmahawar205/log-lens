import gzip
import bz2
import os
from typing import Iterator

class LogReader:
    """
    Ingestion layer supporting streaming reading of potentially very large files.
    """

    @classmethod
    def read_lines(cls, file_path: str) -> Iterator[str]:
        """
        Stream lines from a file efficiently without loading the entire file into memory.
        Supports standard .log/.txt files, as well as .gz and .bz2 compressed files.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        _, ext = os.path.splitext(file_path.lower())

        if ext == '.gz':
            open_func = lambda path: gzip.open(path, 'rt', encoding='utf-8', errors='ignore')
        elif ext == '.bz2':
            open_func = lambda path: bz2.open(path, 'rt', encoding='utf-8', errors='ignore')
        else:
            open_func = lambda path: open(path, 'r', encoding='utf-8', errors='ignore')

        with open_func(file_path) as f:
            for line in f:
                yield line
