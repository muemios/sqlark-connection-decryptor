"""导出：CSV / TXT / TSV / JSON。"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Iterable

from .models import ConnectionRecord

#: CSV/TXT 的列标题
HEADER = ("连接名", "主机", "端口", "用户名", "数据库", "密码", "来源文件")

#: Excel 直接双击打开时不乱码
CSV_ENCODING = "utf-8-sig"


def write_csv(records: Iterable[ConnectionRecord], path: Path) -> int:
    """导出 CSV，返回写入的记录数。"""
    rows = list(records)
    with Path(path).open("w", newline="", encoding=CSV_ENCODING) as fp:
        writer = csv.writer(fp)
        writer.writerow(HEADER)
        for record in rows:
            writer.writerow(record.to_row())
    return len(rows)


def write_txt(records: Iterable[ConnectionRecord], path: Path) -> int:
    """导出便于阅读的纯文本，返回写入的记录数。"""
    rows = list(records)
    lines = [f"# SQLark 连接导出，共 {len(rows)} 条", ""]
    for index, record in enumerate(rows, 1):
        lines.extend(
            [
                f"[{index}] {record.name}",
                f"    地址  : {record.endpoint}",
                f"    用户  : {record.username}",
                f"    类型  : {record.db_type}",
                f"    密码  : {record.password or ''}",
                f"    来源  : {record.source}",
                "",
            ]
        )
    Path(path).write_text("\n".join(lines), encoding=CSV_ENCODING)
    return len(rows)


def records_to_tsv(records: Iterable[ConnectionRecord]) -> str:
    """转换为制表符分隔文本（用于复制到剪贴板/表格软件）。"""
    lines = ["\t".join(HEADER)]
    lines.extend("\t".join(record.to_row()) for record in records)
    return "\n".join(lines)


def write_json(
    records: Iterable[ConnectionRecord], path: Path, include_detail: bool = False
) -> int:
    """导出 JSON；``include_detail`` 为真时附带完整连接参数与属性。"""
    rows = list(records)
    payload = []
    for record in rows:
        item = {
            "name": record.name,
            "host": record.host,
            "port": record.port,
            "username": record.username,
            "dbType": record.db_type,
            "password": record.password,
            "source": str(record.source),
        }
        if include_detail:
            item["detail"] = record.detail
            item["superAttr"] = record.super_attr
            item["sshPassword"] = record.ssh_password
            item["error"] = record.error
        payload.append(item)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return len(rows)
