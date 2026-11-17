"""磁盘检索：自动发现或递归查找 SQLark 连接文件。"""

from __future__ import annotations

import os
import string
from pathlib import Path
from threading import Event
from typing import Callable, Iterator, Optional, Sequence

from .parser import is_connection_xml

#: 明确按文件名识别的连接文件
CANDIDATE_FILENAMES = frozenset(
    {"connectioninfo.xml", "connection-server.xml", "connections.xml"}
)

#: 递归时跳过的目录（体积大或与连接无关）
SKIP_DIR_NAMES = frozenset(
    {
        "node_modules",
        "$recycle.bin",
        "system volume information",
        "windows",
        "winsxs",
        "__pycache__",
        ".git",
        "cache",
        "caches",
        "temp",
        "tmp",
    }
)

ProgressCallback = Optional[Callable[[str], None]]


def _normcase(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def default_search_roots() -> list[tuple[Path, int]]:
    """返回“自动检索”使用的目录及递归深度。

    顺序即检索顺序：先从最可能的位置开始，命中越早越快。
    """
    home = Path.home()
    roots: list[tuple[Path, int]] = [
        (home / ".SQLark", 3),                      # SQLark 本机连接主目录
        (Path(os.environ.get("APPDATA", home)) / "SQLark", 3),
        (Path(os.environ.get("LOCALAPPDATA", home)) / "SQLark", 3),
        (home / "Desktop", 3),
        (home / "Documents", 3),
        (home / "Downloads", 3),
        (home / "OneDrive" / "Desktop", 3),
    ]

    if os.name == "nt":  # 各磁盘下的安装目录
        for drive in string.ascii_uppercase:
            base = Path(f"{drive}:/")
            if not base.exists():
                continue
            for rel in ("Program Files/SQLark", "Program Files (x86)/SQLark", "SQLark"):
                roots.append((base / rel, 4))
    return roots


def iter_connection_files(
    root: Path,
    max_depth: int = 6,
    stop_event: Optional[Event] = None,
) -> Iterator[Path]:
    """递归遍历 ``root``，产出疑似连接文件的 XML 路径。

    Args:
        root: 起始目录。
        max_depth: 最大递归深度（0 表示只看当前目录）。
        stop_event: 置位后尽快停止遍历（供 GUI 的“停止”按钮使用）。
    """
    root = Path(root).resolve()
    base_depth = len(root.parts)
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
        if stop_event is not None and stop_event.is_set():
            return
        current = Path(dirpath)
        if len(current.parts) - base_depth >= max_depth:
            dirnames[:] = []
        dirnames[:] = [
            name for name in dirnames
            if name.lower() not in SKIP_DIR_NAMES and not name.startswith(".")
        ]
        for filename in filenames:
            lower = filename.lower()
            if not lower.endswith(".xml"):
                continue
            if lower not in CANDIDATE_FILENAMES and "connection" not in lower:
                continue
            path = current / filename
            if is_connection_xml(path):
                yield path


def scan_directory(
    root: Path,
    max_depth: int = 8,
    progress: ProgressCallback = None,
    stop_event: Optional[Event] = None,
) -> list[Path]:
    """递归扫描指定目录，返回去重后的连接文件列表。"""
    found: list[Path] = []
    seen: set[str] = set()
    for path in iter_connection_files(root, max_depth=max_depth, stop_event=stop_event):
        if progress:
            progress(f"正在检查：{path.name}")
        key = _normcase(path)
        if key not in seen:
            seen.add(key)
            found.append(path)
    return found


def auto_detect(
    progress: ProgressCallback = None,
    stop_event: Optional[Event] = None,
    roots: Optional[Sequence[tuple[Path, int]]] = None,
) -> list[Path]:
    """检索常见位置，返回去重后的连接文件列表。

    Args:
        progress: 进度回调，参数为可读的状态文本。
        stop_event: 置位后停止检索。
        roots: 自定义检索根目录（默认使用 :func:`default_search_roots`）。
    """
    found: list[Path] = []
    seen: set[str] = set()
    for root, depth in roots if roots is not None else default_search_roots():
        if stop_event is not None and stop_event.is_set():
            break
        if not root.is_dir():
            continue
        if progress:
            progress(f"正在检索：{root}")
        for path in iter_connection_files(root, max_depth=depth, stop_event=stop_event):
            key = _normcase(path)
            if key not in seen:
                seen.add(key)
                found.append(path)
    return found
