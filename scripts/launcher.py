"""PyInstaller 打包入口。

包内的 ``sqlark_decrypt/__main__.py`` 使用相对导入，不能直接作为脚本入口；
本文件提供绝对导入式的启动点。

windowed（无控制台）打包时，``sys.stdout`` / ``sys.stderr`` 为 ``None``，
通过 ``AttachConsole`` 附加到父控制台，使 exe 在命令行下仍可正常输出
``--version`` / ``decrypt`` 等命令的结果。
"""

from __future__ import annotations

import ctypes
import sys


def _attach_parent_console() -> None:
    """Windows：把无控制台 exe 的输出重新接到调用它的终端。"""
    if sys.platform != "win32" or (sys.stdout is not None and sys.stderr is not None):
        return
    try:
        if not ctypes.windll.kernel32.AttachConsole(-1):  # ATTACH_PARENT_PROCESS
            return
        sys.stdout = open("CONOUT$", "w", encoding="utf-8", buffering=1)  # noqa: SIM115
        sys.stderr = open("CONOUT$", "w", encoding="utf-8", buffering=1)  # noqa: SIM115
    except OSError:
        pass


if __name__ == "__main__":
    _attach_parent_console()
    from sqlark_decrypt.cli import main

    sys.exit(main())
