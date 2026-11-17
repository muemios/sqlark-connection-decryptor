"""数据模型：一条数据库连接的解析结果。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


@dataclass
class ConnectionRecord:
    """SQLark 连接文件中的一条连接。

    Attributes:
        source: 记录来源文件。
        name: 连接名（``<connectionName>``）。
        host: 主机名或 IP。
        port: 端口，解析失败时为 ``None``。
        username: 登录用户名。
        db_type: 数据库类型，如 ``ORACLE`` / ``MYSQL`` / ``POSTGRESQL``。
        password: 解密后的明文密码；未保存密码时为 ``None``。
        detail: 第 1 层解密得到的连接参数 JSON（含 salt 等字段）。
        super_attr: ``<superAttr>`` 解密得到的连接属性 JSON。
        error: 该条记录解析失败时的错误信息。
        ssh_password: SSH 隧道密码（若存在且可解密）。
    """

    source: Path
    name: str = ""
    host: str = ""
    port: Optional[int] = None
    username: str = ""
    db_type: str = ""
    password: Optional[str] = None
    detail: Optional[dict[str, Any]] = None
    super_attr: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    ssh_password: Optional[str] = None

    @property
    def endpoint(self) -> str:
        """``host:port`` 形式的地址，端口未知时只返回主机。"""
        if self.port is None:
            return self.host
        return f"{self.host}:{self.port}"

    @property
    def is_ok(self) -> bool:
        """是否成功解析出连接详情。"""
        return self.error is None and self.detail is not None

    def to_row(self) -> tuple[str, str, str, str, str, str, str]:
        """转换为表格/CSV 一行：名称、主机、端口、用户、类型、密码、来源。"""
        return (
            self.name,
            self.host,
            "" if self.port is None else str(self.port),
            self.username,
            self.db_type,
            self.password or "",
            str(self.source),
        )
