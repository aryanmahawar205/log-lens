import pytest
import os
import gzip
import bz2
from app.ingestion.reader import LogReader

def test_log_reader_txt(tmp_path):
    file = tmp_path / "test.txt"
    file.write_text("line1\nline2\n")

    lines = list(LogReader.read_lines(str(file)))
    assert len(lines) == 2
    assert lines[0] == "line1\n"
    assert lines[1] == "line2\n"

def test_log_reader_gz(tmp_path):
    file = tmp_path / "test.gz"
    with gzip.open(str(file), "wt") as f:
        f.write("line1\nline2\n")

    lines = list(LogReader.read_lines(str(file)))
    assert len(lines) == 2

def test_log_reader_bz2(tmp_path):
    file = tmp_path / "test.bz2"
    with bz2.open(str(file), "wt") as f:
        f.write("line1\nline2\n")

    lines = list(LogReader.read_lines(str(file)))
    assert len(lines) == 2
