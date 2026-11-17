"""SQLark（百灵）连接文件解密工具。

本包把 SQLark 保存的数据库连接文件（``connectionInfo.xml`` /
``connection-server.xml``）解析为结构化数据，并还原其中加密保存的密码。

模块划分::

    crypto.py   双层 AES-128-CBC 加解密原语（无业务逻辑）
    models.py   数据模型（ConnectionRecord）
    parser.py   XML 解析 + 组合两层解密，输出 ConnectionRecord
    scanner.py  磁盘检索（自动发现 / 指定目录递归查找）
    export.py   导出 CSV / TXT / TSV
    cli.py      命令行入口（gui / scan / decrypt 三个子命令）
    gui.py      Tkinter 图形界面

典型用法::

    from sqlark_decrypt import scan_directory, parse_file

    for path in scan_directory("~/.SQLark"):
        for record in parse_file(path):
            print(record.name, record.password)
"""

from __future__ import annotations

from .models import ConnectionRecord
from .parser import parse_file, parse_text
from .scanner import auto_detect, scan_directory

__version__ = "0.1.1"

__all__ = [
    "__version__",
    "ConnectionRecord",
    "parse_file",
    "parse_text",
    "scan_directory",
    "auto_detect",
]
