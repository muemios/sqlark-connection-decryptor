"""XML 解析测试：字段提取、双层解密、异常文件处理。"""

from __future__ import annotations

from pathlib import Path

import pytest

from sqlark_decrypt.crypto import encrypt_outer
from sqlark_decrypt.parser import (
    NotConnectionFileError,
    is_connection_xml,
    parse_file,
    parse_text,
)


def test_parse_demo_fixture(demo_fixture: Path) -> None:
    records = parse_file(demo_fixture)

    assert len(records) == 3
    names = [record.name for record in records]
    assert names == ["demo-oracle", "demo-mysql", "demo-postgres"]

    oracle = records[0]
    assert oracle.host == "192.0.2.10"
    assert oracle.port == 1521
    assert oracle.username == "demo_user"
    assert oracle.db_type == "ORACLE"
    assert oracle.password == "Demo#Pass123"
    assert oracle.error is None
    assert oracle.detail is not None
    assert oracle.detail["salt"] == "DEMOsalt00000001"
    assert oracle.super_attr is not None
    assert oracle.super_attr["keepAlive"] is True

    assert records[1].password == "ReadOnly!2024"
    assert records[2].password == "analyst_pw"


def test_parse_file_is_connection_xml(demo_fixture: Path) -> None:
    assert is_connection_xml(demo_fixture) is True


def test_is_connection_xml_rejects_other_xml(tmp_path: Path) -> None:
    other = tmp_path / "other.xml"
    other.write_text("<root><item>1</item></root>", encoding="utf-8")
    assert is_connection_xml(other) is False


def test_parse_text_rejects_other_xml() -> None:
    with pytest.raises(NotConnectionFileError):
        parse_text("<root></root>", Path("x.xml"))


def test_corrupt_detail_keeps_other_fields(tmp_path: Path) -> None:
    xml = (
        '<?xml version="1.0"?><CONNECTIONS version="2.0"><CONNECTION>'
        "<connectionName>bad-detail</connectionName>"
        "<host>192.0.2.99</host><port>1521</port>"
        "<userName>someone</userName><dbType>ORACLE</dbType>"
        "<connectionDetail>not-a-valid-ciphertext</connectionDetail>"
        "</CONNECTION></CONNECTIONS>"
    )
    path = tmp_path / "broken.xml"
    path.write_text(xml, encoding="utf-8")

    records = parse_file(path)
    assert len(records) == 1
    record = records[0]
    assert record.name == "bad-detail"
    assert record.host == "192.0.2.99"
    assert record.port == 1521
    assert record.error is not None
    assert record.password is None


def test_parse_handles_xml_escaped_ciphertext(tmp_path: Path) -> None:
    """SQLark 导出时对 Base64 做了 XML 转义，解析时应还原。"""
    ciphertext = encrypt_outer('{"dbType":"ORACLE"}')
    escaped = ciphertext.replace("&", "&amp;").replace("<", "&lt;")
    xml = (
        "<CONNECTIONS><CONNECTION>"
        f"<connectionDetail>{escaped}</connectionDetail>"
        "</CONNECTION></CONNECTIONS>"
    )
    records = parse_text(xml, Path("inline.xml"))
    assert records[0].detail == {"dbType": "ORACLE"}
