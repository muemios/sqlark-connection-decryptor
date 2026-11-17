"""命令行入口测试。"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from sqlark_decrypt.cli import main


def test_decrypt_prints_table(demo_fixture: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["decrypt", str(demo_fixture)])

    output = capsys.readouterr().out
    assert code == 0
    assert "demo-oracle" in output
    assert "Demo#Pass123" in output


def test_decrypt_mask_hides_password(demo_fixture: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["decrypt", str(demo_fixture), "--mask"])

    output = capsys.readouterr().out
    assert code == 0
    assert "Demo#Pass123" not in output
    assert "****" in output


def test_decrypt_exports_files(
    demo_fixture: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    csv_path = tmp_path / "out.csv"
    txt_path = tmp_path / "out.txt"
    json_path = tmp_path / "out.json"

    code = main(
        ["decrypt", str(demo_fixture), "--csv", str(csv_path),
         "--txt", str(txt_path), "--json", str(json_path)]
    )

    assert code == 0
    assert csv_path.exists() and txt_path.exists() and json_path.exists()
    assert "Demo#Pass123" in csv_path.read_text(encoding="utf-8-sig")


def test_decrypt_skips_non_connection_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    junk = tmp_path / "junk.xml"
    junk.write_text("<root/>", encoding="utf-8")

    code = main(["decrypt", str(junk)])

    stderr = capsys.readouterr().err
    assert code == 1
    assert "跳过" in stderr


def test_scan_lists_files(tmp_path: Path, demo_fixture: Path, capsys: pytest.CaptureFixture[str]) -> None:
    shutil.copy(demo_fixture, tmp_path / "connectionInfo.xml")

    code = main(["scan", str(tmp_path)])

    output = capsys.readouterr().out
    assert code == 0
    assert "connectionInfo.xml" in output


def test_scan_returns_error_when_nothing_found(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = main(["scan", str(tmp_path)])

    assert code == 1
    assert "未找到" in capsys.readouterr().err


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--version"])
    assert excinfo.value.code == 0
    assert "sqlark-decrypt" in capsys.readouterr().out

