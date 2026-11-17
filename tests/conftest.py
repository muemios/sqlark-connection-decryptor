"""pytest 公共配置。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # 未 pip install -e . 时也能导入包
    sys.path.insert(0, str(ROOT))

FIXTURE = ROOT / "tests" / "fixtures" / "demo-connections.xml"


@pytest.fixture(scope="session")
def demo_fixture() -> Path:
    """脱敏演示连接文件（由 scripts/make_fixture.py 生成）。"""
    if not FIXTURE.exists():
        import subprocess

        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "make_fixture.py")],
            check=True,
            cwd=str(ROOT),
        )
    assert FIXTURE.exists(), "缺少测试夹具 tests/fixtures/demo-connections.xml"
    return FIXTURE
