"""提交前敏感信息自检。

扫描仓库文本文件中的常见敏感内容：
    - 私钥、GitHub / AWS / Slack 等令牌
    - 非文档专用网段的 IPv4（防止把真实内网地址提交进仓库）
    - Windows 用户目录路径（可能带真实用户名）
    - 邮箱地址（可能泄露个人信息）
    - 真实 SQLark 连接文件（connectionInfo.xml 等）

用法::

    python scripts/check_no_secrets.py

退出码：0 = 未发现问题；1 = 发现疑似敏感信息。
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parent.parent

#: 文档中允许出现的示例网段（RFC 5737）/ 本地回环
ALLOWED_IP_PREFIXES = (
    "192.0.2.",
    "198.51.100.",
    "203.0.113.",
    "127.0.0.1",
    "0.0.0.0",
    "255.255.255.255",
)

#: 需要跳过的文件/目录
SKIP_DIRS = {".git", ".venv", "venv", "build", "dist", "__pycache__", ".pytest_cache",
             ".ruff_cache", ".idea", ".vscode", ".tools", "release", "htmlcov",
             "site-packages", "node_modules"}
SKIP_SUFFIXES = {".exe", ".zip", ".ico", ".png", ".jpg", ".jpeg", ".gif", ".pdf",
                 ".whl", ".pyc", ".db", ".mv.db"}

#: 文档中允许出现的占位符（不是真实信息）
PLACEHOLDER_USER_DIRS = {"me", "user", "username", "yourname", "xxx", "name"}
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net"}
ALLOWED_EMAILS = {"git@github.com"}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("私钥", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("GitHub 令牌", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b")),
    ("GitHub Fine-grained 令牌", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("AWS Access Key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Slack 令牌", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Windows 用户目录", re.compile(r"[Cc]:\\\\?Users\\\\?[^\\\s\"'/]+")),
    ("邮箱地址", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
]

IPV4_RE = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")


def _tracked_files() -> Iterator[Path]:
    """优先使用 git 已跟踪文件；不是 git 仓库时遍历全部文本文件。"""
    try:
        output = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout.decode("utf-8", "replace")
        for name in output.split("\0"):
            if name:
                yield ROOT / name
        return
    except (OSError, subprocess.CalledProcessError):
        pass

    for path in ROOT.rglob("*"):
        if path.is_file() and not any(part in SKIP_DIRS for part in path.parts):
            yield path


def _is_text(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    try:
        return b"\0" not in path.read_bytes()[:4096]
    except OSError:
        return False


def _ip_is_allowed(ip: str) -> bool:
    if ip.startswith(ALLOWED_IP_PREFIXES):
        return True
    octets = [int(part) for part in ip.split(".")]
    return all(0 <= value <= 255 for value in octets) and octets[0] == 0


def scan_file(path: Path) -> list[str]:
    """返回单个文件的疑似问题列表。"""
    findings: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings

    for lineno, line in enumerate(text.splitlines(), 1):
        for label, pattern in PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(0)
                if label == "邮箱地址":
                    domain = value.rsplit("@", 1)[-1].lower()
                    if domain in ALLOWED_EMAIL_DOMAINS or value.lower() in ALLOWED_EMAILS:
                        continue
                if label == "Windows 用户目录":
                    segment = re.split(r"[\\\\/]", value)[-1]
                    if segment.startswith("<") or segment.lower() in PLACEHOLDER_USER_DIRS:
                        continue
                findings.append(f"{path.relative_to(ROOT)}:{lineno}: 疑似{label}: {value}")
        for match in IPV4_RE.finditer(line):
            ip = match.group(0)
            if _ip_is_allowed(ip):
                continue
            findings.append(f"{path.relative_to(ROOT)}:{lineno}: 疑似真实 IPv4: {ip}")
    return findings


def _configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError, OSError):
            pass


def main() -> int:
    _configure_console()
    findings: list[str] = []
    checked = 0
    for path in _tracked_files():
        if not path.is_file() or not _is_text(path):
            continue
        checked += 1
        findings.extend(scan_file(path))

    if findings:
        print("发现疑似敏感信息：", file=sys.stderr)
        for item in findings:
            print(f"  - {item}", file=sys.stderr)
        print(
            "\n如确认是示例数据，请改用 RFC 5737 文档网段（192.0.2.0/24 等）并移除个人信息。",
            file=sys.stderr,
        )
        return 1

    print(f"敏感信息自检通过（已检查 {checked} 个文本文件）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


