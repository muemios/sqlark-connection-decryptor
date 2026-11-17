"""导出功能测试：CSV / TXT / TSV / JSON。"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from sqlark_decrypt.export import records_to_tsv, write_csv, write_json, write_txt
from sqlark_decrypt.parser import parse_file


def test_write_csv(tmp_path: Path, demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)
    target = tmp_path / "out.csv"

    assert write_csv(records, target) == 3

    with target.open(encoding="utf-8-sig", newline="") as fp:
        rows = list(csv.reader(fp))
    assert rows[0] == ["连接名", "主机", "端口", "用户名", "数据库", "密码", "来源文件"]
    assert rows[1][0] == "demo-oracle"
    assert rows[1][5] == "Demo#Pass123"


def test_write_txt(tmp_path: Path, demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)
    target = tmp_path / "out.txt"

    assert write_txt(records, target) == 3
    text = target.read_text(encoding="utf-8-sig")
    assert "demo-mysql" in text
    assert "ReadOnly!2024" in text
    assert "198.51.100.24:3306" in text


def test_records_to_tsv(demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)
    text = records_to_tsv(records)
    lines = text.splitlines()
    assert lines[0].split("\t")[0] == "连接名"
    assert len(lines) == 4


def test_write_json_without_detail(tmp_path: Path, demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)
    target = tmp_path / "out.json"

    assert write_json(records, target) == 3
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload[0]["name"] == "demo-oracle"
    assert payload[0]["password"] == "Demo#Pass123"
    assert "detail" not in payload[0]


def test_write_json_with_detail(tmp_path: Path, demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)
    target = tmp_path / "out-full.json"

    write_json(records, target, include_detail=True)
    payload = json.loads(target.read_text(encoding="utf-8"))
    assert payload[1]["detail"]["salt"] == "DEMOsalt00000002"
    assert payload[1]["detail"]["password_plain"] == "ReadOnly!2024"
