"""命令行入口：``sqlark-decrypt {gui,scan,decrypt}``。"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from pathlib import Path
from typing import Iterable, Optional, Sequence

from . import __version__
from .export import write_csv, write_json, write_txt
from .models import ConnectionRecord
from .parser import NotConnectionFileError, parse_file
from .scanner import auto_detect, scan_directory


# --------------------------------------------------------------------------- #
# 输出
# --------------------------------------------------------------------------- #
def _mask(password: Optional[str]) -> str:
    if not password:
        return ""
    return "*" * min(len(password), 12)


def _display_width(text: str) -> int:
    """近似计算终端显示宽度：CJK 全角字符按 2 列计。"""
    return sum(2 if unicodedata.east_asian_width(char) in ("W", "F") else 1 for char in text)


def _pad(text: object, width: int) -> str:
    value = str(text)
    return value + " " * max(0, width - _display_width(value))


def _print_table(records: Iterable[ConnectionRecord], mask: bool) -> None:
    rows = list(records)
    if not rows:
        return
    headers = ("连接名", "主机", "端口", "用户名", "数据库", "密码")
    table = [
        (
            r.name,
            r.host,
            "" if r.port is None else str(r.port),
            r.username,
            r.db_type,
            _mask(r.password) if mask else (r.password or ""),
        )
        for r in rows
    ]
    widths = [
        max(_display_width(str(row[i])) for row in (*table, headers)) for i in range(len(headers))
    ]
    line = "  ".join(_pad(title, widths[i]) for i, title in enumerate(headers))
    print(line)
    print("-" * _display_width(line))
    for row, record in zip(table, rows):
        print("  ".join(_pad(cell, widths[i]) for i, cell in enumerate(row)))
        if record.error:
            print(f"  [警告] {record.error}", file=sys.stderr)


# --------------------------------------------------------------------------- #
# 子命令
# --------------------------------------------------------------------------- #
def cmd_gui(args: argparse.Namespace) -> int:
    try:
        from .gui import run as run_gui
    except ImportError as exc:  # 没有 tkinter 的环境（如精简 Linux）
        print(f"无法启动图形界面: {exc}", file=sys.stderr)
        return 1
    initial = [Path(p) for p in args.open]
    try:
        run_gui(initial_files=initial, autoload=args.autoload)
    except Exception as exc:  # 例如没有图形环境（Linux 无 DISPLAY）
        print(f"图形界面启动失败: {exc}", file=sys.stderr)
        print("可改用命令行：sqlark-decrypt decrypt <文件>", file=sys.stderr)
        return 1
    return 0


def cmd_scan(args: argparse.Namespace) -> int:
    files: list[Path] = list(args.paths)
    if args.auto or not files:
        files = auto_detect(progress=lambda msg: print(msg, file=sys.stderr))
    else:
        files = [p for path in files for p in scan_directory(Path(path))]
        files = list(dict.fromkeys(files))

    if not files:
        print("未找到 SQLark 连接文件。可指定目录：sqlark-decrypt scan <目录>", file=sys.stderr)
        return 1
    for path in files:
        print(path)
    if args.json:
        args.json.write_text(
            json.dumps([str(p) for p in files], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    return 0


def _collect(files: Sequence[Path]) -> tuple[list[ConnectionRecord], list[tuple[Path, str]]]:
    records: list[ConnectionRecord] = []
    errors: list[tuple[Path, str]] = []
    for path in files:
        try:
            records.extend(parse_file(path))
        except NotConnectionFileError as exc:
            errors.append((path, str(exc)))
        except OSError as exc:
            errors.append((path, f"读取失败: {exc}"))
    return records, errors


def cmd_decrypt(args: argparse.Namespace) -> int:
    records, errors = _collect([Path(p) for p in args.files])
    for path, message in errors:
        print(f"[跳过] {path}: {message}", file=sys.stderr)

    if not args.quiet:
        _print_table(records, mask=args.mask)

    if args.csv:
        write_csv(records, args.csv)
        print(f"已导出 CSV: {args.csv}", file=sys.stderr)
    if args.txt:
        write_txt(records, args.txt)
        print(f"已导出 TXT: {args.txt}", file=sys.stderr)
    if args.json:
        write_json(records, args.json, include_detail=args.raw)
        print(f"已导出 JSON: {args.json}", file=sys.stderr)
    if args.raw and not args.quiet:
        for record in records:
            if record.detail:
                print(f"\n== {record.name} 连接参数 ==")
                print(json.dumps(record.detail, ensure_ascii=False, indent=2))

    if not records:
        return 1
    return 2 if errors else 0


# --------------------------------------------------------------------------- #
# 解析器
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlark-decrypt",
        description="SQLark（百灵）连接文件批量解密工具：还原加密保存的数据库密码。",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    gui = sub.add_parser("gui", help="启动图形界面（默认）")
    gui.add_argument("--open", action="append", default=[], metavar="FILE",
                     help="启动时加载指定连接文件，可重复")
    gui.add_argument("--autoload", action="store_true", help="启动后立即自动检索")
    gui.set_defaults(func=cmd_gui)

    scan = sub.add_parser("scan", help="查找 SQLark 连接文件")
    scan.add_argument("paths", nargs="*", type=Path, help="要扫描的目录（默认自动检索）")
    scan.add_argument("--auto", action="store_true", help="使用内置的自动检索路径")
    scan.add_argument("--json", type=Path, help="把文件清单写入 JSON")
    scan.set_defaults(func=cmd_scan)

    dec = sub.add_parser("decrypt", help="解密并输出连接信息")
    dec.add_argument("files", nargs="+", type=Path, help="connectionInfo.xml 等连接文件")
    dec.add_argument("--raw", action="store_true", help="同时打印完整连接参数 JSON")
    dec.add_argument("--mask", action="store_true", help="表格中隐藏密码")
    dec.add_argument("--quiet", action="store_true", help="不打印表格")
    dec.add_argument("--csv", type=Path, help="导出 CSV")
    dec.add_argument("--txt", type=Path, help="导出 TXT")
    dec.add_argument("--json", type=Path, help="导出 JSON")
    dec.set_defaults(func=cmd_decrypt)
    return parser


def _configure_console() -> None:
    """管道/重定向到现代终端时统一用 UTF-8，避免 Windows 下中文乱码。"""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数；返回进程退出码。"""
    _configure_console()
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        # 无参数时启动 GUI（双击 exe 的体验）
        return cmd_gui(argparse.Namespace(open=[], autoload=False))
    return int(args.func(args))


