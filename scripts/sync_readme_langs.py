"""同步所有 README 的语言切换栏。

在 `scripts/readme_langs.py` 的 LANGUAGES 中维护语言清单后运行本脚本，
它会：
    1. 找到每个 README 的一级标题；
    2. 用统一的语言栏替换其后的旧语言栏（或 `<!-- LANG-BAR -->` 占位符）；
    3. 保证标题、语言栏、正文之间空行规范。

用法::

    python scripts/sync_readme_langs.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readme_langs import LANGUAGES, ROOT, language_bar  # noqa: E402


def _find_title_index(lines: list[str]) -> int | None:
    for index, line in enumerate(lines):
        if line.startswith("# "):
            return index
    return None


def sync_file(path: Path) -> str:
    """同步单个文件，返回 'updated' / 'unchanged' / 'skipped'。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    title_index = _find_title_index(lines)
    if title_index is None:
        return "skipped"

    bar = language_bar(path.name)
    rest = lines[title_index + 1:]
    while rest and not rest[0].strip():
        rest.pop(0)
    if rest and ("README." in rest[0] or "LANG-BAR" in rest[0]):
        rest.pop(0)
    while rest and not rest[0].strip():
        rest.pop(0)

    new_lines = lines[: title_index + 1] + ["", bar, ""] + rest
    content = "\n".join(new_lines) + "\n"
    if content == path.read_text(encoding="utf-8"):
        return "unchanged"
    path.write_text(content, encoding="utf-8")
    return "updated"


def main() -> int:
    updated = 0
    for _, filename in LANGUAGES:
        path = ROOT / filename
        if not path.exists():
            print(f"[missing] {filename}")
            continue
        result = sync_file(path)
        print(f"[{result}] {filename}")
        if result == "updated":
            updated += 1
    print(f"done: {updated} file(s) updated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
