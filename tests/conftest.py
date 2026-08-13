from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def write_show(tmp_path: Path):
    def write_show_file(contents: str, name: str = "show.toml") -> Path:
        path = tmp_path / name
        path.write_text(contents, encoding="utf-8")
        return path

    return write_show_file
