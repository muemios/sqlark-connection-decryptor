"""生成脱敏的演示/测试连接文件（tests/fixtures/demo-connections.xml）。

文件中的所有主机、用户名、密码都是虚构的示例数据：
主机使用 RFC 5737 文档专用地址段（192.0.2.0/24、198.51.100.0/24、203.0.113.0/24）。

用法::

    python scripts/make_fixture.py [输出路径]
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlark_decrypt.crypto import encrypt_outer, encrypt_secret  # noqa: E402

# 演示数据：主机为文档专用网段，密码为虚构示例
DEMO_CONNECTIONS = [
    {
        "name": "demo-oracle",
        "host": "192.0.2.10",
        "port": 1521,
        "user": "demo_user",
        "dbType": "ORACLE",
        "dbVersion": "12",
        "password": "Demo#Pass123",
        "salt": "DEMOsalt00000001",
        "url": "jdbc:oracle:thin:@192.0.2.10:1521/DEMO",
        "sort": 1,
    },
    {
        "name": "demo-mysql",
        "host": "198.51.100.24",
        "port": 3306,
        "user": "demo_reader",
        "dbType": "MYSQL",
        "dbVersion": "8",
        "password": "ReadOnly!2024",
        "salt": "DEMOsalt00000002",
        "url": "jdbc:mysql://198.51.100.24:3306/demo",
        "sort": 2,
    },
    {
        "name": "demo-postgres",
        "host": "203.0.113.5",
        "port": 5432,
        "user": "analyst",
        "dbType": "POSTGRESQL",
        "dbVersion": "15",
        "password": "analyst_pw",
        "salt": "DEMOsalt00000003",
        "url": "jdbc:postgresql://203.0.113.5:5432/demo",
        "sort": 3,
    },
]

SUPER_ATTR = {
    "keepAlive": True,
    "keepAliveInterval": 240,
    "autoReconnected": True,
    "autoReConnectCount": 1,
    "commit": "manual",
    "execScript": True,
}


def _build_detail(item: dict) -> dict:
    """构造与 SQLark 导出一致的连接参数 JSON（密码为第 2 层密文）。"""
    return {
        "dbType": item["dbType"],
        "dbVersion": item["dbVersion"],
        "connectionType": "normal",
        "host": item["host"],
        "port": item["port"],
        "user": item["user"],
        "password": encrypt_secret(item["password"], item["salt"]),
        "connectWay": "url",
        "url": item["url"],
        "salt": item["salt"],
        "sshOpen": False,
        "sshConnModel": None,
        "sslOpen": False,
        "sslConnModel": None,
        "rememberPassword": True,
        "driverOptions": {},
        "defaultOptions": {},
        "serviceName": "DEMO",
    }


def _connection_xml(item: dict) -> str:
    detail = encrypt_outer(json.dumps(_build_detail(item), ensure_ascii=False))
    super_attr = encrypt_outer(json.dumps(SUPER_ATTR, ensure_ascii=False))
    return f"""<CONNECTION>
<connectionName>{item['name']}</connectionName>
<host>{item['host']}</host>
<port>{item['port']}</port>
<userName>{item['user']}</userName>
<dbType>{item['dbType']}</dbType>
<dbVersion>{item['dbVersion']}</dbVersion>
<connectionType>DEFAULT</connectionType>
<connectionDetail>{html.escape(detail)}</connectionDetail>
<state>0</state>
<sort>{item['sort']}</sort>
<rememberPassword>1</rememberPassword>
<isProduce>0</isProduce>
<superAttr>{html.escape(super_attr)}</superAttr>
</CONNECTION>"""


def build_xml() -> str:
    body = "\n".join(_connection_xml(item) for item in DEMO_CONNECTIONS)
    return (
        '<?xml version="1.0" standalone="yes"?>\n'
        '<CONNECTIONS version="2.0">\n'
        f"{body}\n"
        "</CONNECTIONS>\n"
    )


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def main() -> int:
    _configure_console()
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests" / "fixtures" / "demo-connections.xml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_xml(), encoding="utf-8")
    print(f"已生成演示连接文件: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

