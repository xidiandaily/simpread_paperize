"""init 子命令。"""

from pathlib import Path

import pytest
import yaml

from simpread_paperize.book.init_manifest import MANIFEST_FILENAME, write_manifest_template


def test_init_creates_template(tmp_path: Path) -> None:
    write_manifest_template(tmp_path)
    mf = tmp_path / MANIFEST_FILENAME
    assert mf.is_file()
    data = yaml.safe_load(mf.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert "book" in data and "volumes" in data


def test_init_refuse_overwrite(tmp_path: Path) -> None:
    write_manifest_template(tmp_path)
    with pytest.raises(FileExistsError):
        write_manifest_template(tmp_path, force=False)


def test_init_force(tmp_path: Path) -> None:
    write_manifest_template(tmp_path)
    write_manifest_template(tmp_path, force=True)
    assert (tmp_path / MANIFEST_FILENAME).is_file()
