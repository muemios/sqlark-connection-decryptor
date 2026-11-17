"""跨平台单文件构建脚本（PyInstaller）。

产物命名规范（便于在 Release 中区分平台/架构）::

    sqlark-connection-decryptor-v<版本>-<平台>-<架构>.exe        # Windows GUI
    sqlark-connection-decryptor-cli-v<版本>-<平台>-<架构>[.exe]  # 命令行版

    平台: windows | linux | macos
    架构: x64 | arm64 | x86 | arm

示例::

    python scripts/build_binary.py --variant gui     # Windows 图形界面版
    python scripts/build_binary.py --variant cli     # 命令行版（各平台均可用）

说明：
    - 版本号唯一来源是 ``sqlark_decrypt/__version__``；
    - Windows GUI 使用 ``--windowed`` 并打包图标，命令行版使用 ``--console``；
    - Linux/macOS 只构建命令行版（PyInstaller 单文件，无窗口依赖）。
"""

from __future__ import annotations

import argparse
import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlark_decrypt import __version__  # noqa: E402

PLATFORM_MAP = {"win32": "windows", "linux": "linux", "darwin": "macos"}
ARCH_MAP = {
    "x86_64": "x64", "amd64": "x64",
    "aarch64": "arm64", "arm64": "arm64",
    "i386": "x86", "i686": "x86",
    "armv7l": "arm", "armv7": "arm",
}


def detect_platform() -> str:
    if sys.platform not in PLATFORM_MAP:
        raise SystemExit(f"Unsupported operating system: {sys.platform}")
    return PLATFORM_MAP[sys.platform]


def detect_arch() -> str:
    machine = platform.machine().lower()
    if machine not in ARCH_MAP:
        raise SystemExit(f"Unsupported CPU architecture: {machine}")
    return ARCH_MAP[machine]


def artifact_name(platform_name: str, arch: str, variant: str, version: str) -> str:
    """生成 `sqlark-connection-decryptor[-cli]-v<ver>-<platform>-<arch>` 名称（不含扩展名）。"""
    suffix = "" if variant == "gui" else "-cli"
    return f"sqlark-connection-decryptor{suffix}-v{version}-{platform_name}-{arch}"


def build(platform_name: str, arch: str, variant: str, version: str) -> Path:
    name = artifact_name(platform_name, arch, variant, version)
    entry = ROOT / "scripts" / "launcher.py"

    # PyInstaller 的 --add-data 分隔符：Windows 为 ';'，POSIX 为 ':'
    data_sep = ";" if os.name == "nt" else ":"
    args = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onefile",
        "--console" if variant == "cli" else "--windowed",
        "--name", name,
        "--distpath", str(ROOT / "dist"),
        "--workpath", str(ROOT / "build" / "pyinstaller"),
        "--specpath", str(ROOT / "build" / "pyinstaller"),
        "--add-data", f"{ROOT / 'assets'}{data_sep}assets",
    ]
    if platform_name == "windows":
        args += ["--icon", str(ROOT / "assets" / "sqlark.ico")]

    args.append(str(entry))
    print("PyInstaller:", " ".join(args), flush=True)
    subprocess.run(args, cwd=ROOT, check=True)

    # 注意：版本号中的点会让 Path.stem 误判后缀，因此按完整文件名匹配
    for candidate in (ROOT / "dist" / name, ROOT / "dist" / f"{name}.exe"):
        if candidate.is_file():
            return candidate
    raise SystemExit(f"Build finished but artifact not found: {name}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="构建 SQLark 连接解密工具单文件产物")
    parser.add_argument("--variant", choices=["gui", "cli"], default="gui",
                        help="gui=图形界面版（仅 Windows），cli=命令行版（全平台）")
    parser.add_argument("--version", default=__version__, help="覆盖版本号（默认取包版本）")
    parser.add_argument("--print-name", action="store_true", help="只打印产物名后退出")
    args = parser.parse_args()

    platform_name, arch = detect_platform(), detect_arch()
    if args.variant == "gui" and platform_name != "windows":
        # 非 Windows 平台只发布命令行版，避免依赖桌面环境
        raise SystemExit("The gui variant is Windows-only; use --variant cli on other platforms")

    name = artifact_name(platform_name, arch, args.variant, args.version)
    if args.print_name:
        print(name)
        return 0

    target = build(platform_name, arch, args.variant, args.version)
    print(f"\nArtifact : {target}")
    print(f"Platform : {platform_name}")
    print(f"Arch     : {arch}")
    print(f"Variant  : {args.variant}")
    print(f"SHA256   : {sha256(target)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
