"""SQLark 连接 XML 解析：读取字段、组合两层解密、产出 ConnectionRecord。"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Optional

from .crypto import DecryptionError, decrypt_outer, decrypt_secret
from .models import ConnectionRecord

#: 判定文件是否为 SQLark 连接文件的标记（开始 + 结束标签都要有）
CONNECTIONS_MARKER = b"<CONNECTIONS"
CONNECTIONS_END_MARKER = b"</CONNECTIONS>"

#: 单个 <CONNECTION> 块
_CONNECTION_RE = re.compile(r"<CONNECTION>(.*?)</CONNECTION>", re.S)

#: 连接文件体积上限（防止误把大文件当连接文件读取）
MAX_FILE_SIZE = 8 * 1024 * 1024


class NotConnectionFileError(ValueError):
    """文件不是 SQLark 连接文件（缺少 <CONNECTIONS> 根节点）。"""


def is_connection_xml(path: Path, max_size: int = MAX_FILE_SIZE) -> bool:
    """快速判断文件是否是 SQLark 连接文件（检查首尾标记，不解析 XML）。"""
    try:
        size = path.stat().st_size
        if size > max_size:
            return False
        with path.open("rb") as fp:
            head = fp.read(64 * 1024)
            if CONNECTIONS_MARKER not in head:
                return False
            if CONNECTIONS_END_MARKER in head:
                return True
            tail_start = max(0, size - 4096)
            if tail_start <= len(head):
                return False
            fp.seek(tail_start)
            return CONNECTIONS_END_MARKER in fp.read()
    except OSError:
        return False


def _field(block: str, name: str) -> Optional[str]:
    """取 ``<name>...</name>`` 的内容，做 XML 反转义并去除首尾空白。"""
    match = re.search(rf"<{name}>(.*?)</{name}>", block, re.S)
    if not match:
        return None
    return html.unescape(match.group(1)).strip()


def _parse_json(value: Optional[str]) -> Optional[dict[str, Any]]:
    if not value:
        return None
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _apply_inner_secrets(detail: dict[str, Any]) -> None:
    """原地给 detail 及其 ssh/ssl 子对象补上 ``*_plain`` 明文密码字段。"""
    if detail.get("password"):
        detail["password_plain"] = decrypt_secret(detail["password"], detail.get("salt"))

    for model_key in ("sshConnModel", "sslConnModel"):
        model = detail.get(model_key)
        if not isinstance(model, dict):
            continue
        for pwd_key in ("sshPassword", "sslPassword", "passphrase"):
            if model.get(pwd_key):
                model[f"{pwd_key}_plain"] = decrypt_secret(model[pwd_key], model.get("salt"))


def _build_record(block: str, source: Path) -> ConnectionRecord:
    host = _field(block, "host") or ""
    port_text = _field(block, "port") or ""
    record = ConnectionRecord(
        source=source,
        name=_field(block, "connectionName") or "",
        host=host,
        port=int(port_text) if port_text.isdigit() else None,
        username=_field(block, "userName") or "",
        db_type=_field(block, "dbType") or "",
    )

    detail_text = _field(block, "connectionDetail")
    if detail_text:
        try:
            detail = _parse_json(decrypt_outer(detail_text))
            if detail is None:
                raise DecryptionError("第 1 层解密结果不是合法 JSON")
            _apply_inner_secrets(detail)
            record.detail = detail
            record.password = detail.get("password_plain")
            record.db_type = record.db_type or str(detail.get("dbType", ""))
            record.name = record.name or str(detail.get("connectName") or "")
            record.username = record.username or str(detail.get("user") or "")
            record.host = record.host or str(detail.get("host") or "")
        except (DecryptionError, ValueError, TypeError) as exc:
            record.error = f"connectionDetail 解析失败: {exc}"

    super_attr_text = _field(block, "superAttr")
    if super_attr_text:
        try:
            record.super_attr = _parse_json(decrypt_outer(super_attr_text))
        except (DecryptionError, ValueError, TypeError):
            # superAttr 只是连接属性，失败不影响密码提取
            record.super_attr = None

    ssh_text = _field(block, "sshDetail")
    if ssh_text and record.detail is not None:
        try:
            ssh_detail = _parse_json(decrypt_outer(ssh_text)) or {}
            pwd = decrypt_secret(str(ssh_detail.get("sshPassword") or ""), ssh_detail.get("salt"))
            record.ssh_password = pwd or None
        except (DecryptionError, ValueError, TypeError):
            record.ssh_password = None

    return record


def parse_text(text: str, source: Path) -> list[ConnectionRecord]:
    """解析 XML 文本，返回其中的全部连接。

    Raises:
        NotConnectionFileError: 文本不是 SQLark 连接文件。
    """
    if "<CONNECTIONS" not in text:
        raise NotConnectionFileError(f"不是 SQLark 连接文件: {source}")
    return [_build_record(block, source) for block in _CONNECTION_RE.findall(text)]


def parse_file(path: Path) -> list[ConnectionRecord]:
    """读取并解析连接文件。

    Raises:
        NotConnectionFileError: 文件不是 SQLark 连接文件。
        FileNotFoundError / OSError: 文件无法读取。
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_text(text, path)

