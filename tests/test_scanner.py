"""目录检索测试。"""

from __future__ import annotations

import shutil
from pathlib import Path

from sqlark_decrypt.scanner import auto_detect, iter_connection_files, scan_directory


def _prepare_tree(tmp_path: Path, demo_fixture: Path) -> Path:
    """构造：根目录 1 个连接文件、嵌套目录 1 个、无关文件若干。"""
    root = tmp_path / "data"
    (root / "sub" / "deeper").mkdir(parents=True)

    shutil.copy(demo_fixture, root / "connectionInfo.xml")
    shutil.copy(demo_fixture, root / "sub" / "deeper" / "connection-server.xml")

    (root / "other.xml").write_text("<root/>", encoding="utf-8")
    (root / "notes.txt").write_text("not xml", encoding="utf-8")
    (root / "sub" / "broken-connection.xml").write_text("<CONNECTIONS>", encoding="utf-8")
    return root


def test_scan_directory_finds_connection_files(tmp_path: Path, demo_fixture: Path) -> None:
    root = _prepare_tree(tmp_path, demo_fixture)

    found = scan_directory(root, max_depth=8)

    assert len(found) == 2
    assert {path.name for path in found} == {"connectionInfo.xml", "connection-server.xml"}


def test_scan_directory_respects_max_depth(tmp_path: Path, demo_fixture: Path) -> None:
    root = _prepare_tree(tmp_path, demo_fixture)

    shallow = scan_directory(root, max_depth=1)

    assert len(shallow) == 1
    assert shallow[0].name == "connectionInfo.xml"


def test_scan_directory_missing_root_returns_empty(tmp_path: Path) -> None:
    assert scan_directory(tmp_path / "does-not-exist") == []


def test_auto_detect_with_custom_roots(tmp_path: Path, demo_fixture: Path) -> None:
    root = _prepare_tree(tmp_path, demo_fixture)

    found = auto_detect(roots=[(root, 8)])

    assert len(found) == 2


def test_auto_detect_stops_on_event(tmp_path: Path, demo_fixture: Path) -> None:
    import threading

    root = _prepare_tree(tmp_path, demo_fixture)
    stop = threading.Event()
    stop.set()

    assert auto_detect(roots=[(root, 8)], stop_event=stop) == []


def test_iter_connection_files_skips_heavy_dirs(tmp_path: Path, demo_fixture: Path) -> None:
    root = tmp_path / "data"
    (root / "node_modules" / "pkg").mkdir(parents=True)
    shutil.copy(demo_fixture, root / "node_modules" / "pkg" / "connectionInfo.xml")

    assert list(iter_connection_files(root, max_depth=8)) == []
