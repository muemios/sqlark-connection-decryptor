"""检查多语言 README 的一致性（CI 与本地都会运行）。

校验内容：
    - 每种语言的 README 文件都存在；
    - 每个 README 都有一行完整的语言切换栏；
    - 语言栏链接集合 = 除自身外的全部语言文件（不多不少）；
    - 当前语言以加粗形式出现；
    - 没有遗留 `<!-- LANG-BAR -->` 占位符。

用法::

    python scripts/check_i18n.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from readme_langs import LANGUAGES, ROOT  # noqa: E402

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # noqa: SLF001
    except (AttributeError, ValueError, OSError):
        pass

_LINK_RE = re.compile(r"\]\((README[^)#]*\.md)\)")


def _language_bar_line(text: str) -> str | None:
    for line in text.splitlines():
        if "](README" in line and "·" in line:
            return line
    return None


def check() -> list[str]:
    """返回错误列表；空列表表示通过。"""
    errors: list[str] = []
    filenames = [filename for _, filename in LANGUAGES]

    for label, filename in LANGUAGES:
        path = ROOT / filename
        if not path.exists():
            errors.append(f"missing file: {filename}")
            continue

        text = path.read_text(encoding="utf-8")
        if "LANG-BAR" in text:
            errors.append(f"{filename}: LANG-BAR placeholder still present, run sync_readme_langs.py")
            continue

        bar = _language_bar_line(text)
        if bar is None:
            errors.append(f"{filename}: language bar not found")
            continue

        expected = set(filenames) - {filename}
        actual = set(_LINK_RE.findall(bar))
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            errors.append(f"{filename}: language bar links mismatch missing={missing} extra={extra}")

        if f"**{label}**" not in bar:
            errors.append(f"{filename}: current language is not bold (expected **{label}**)")

        if not text.startswith("# "):
            errors.append(f"{filename}: missing top-level heading")

    return errors


def main() -> int:
    errors = check()
    if errors:
        print("i18n README check failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"i18n README check passed ({len(LANGUAGES)} languages: {', '.join(f for _, f in LANGUAGES)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
