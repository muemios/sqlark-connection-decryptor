"""README 多语言清单（`sync_readme_langs.py` / `check_i18n.py` 共用）。

新增语言时只需在此处追加一行，然后运行::

    python scripts/sync_readme_langs.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: (语言显示名, README 文件名)，顺序即语言栏中的顺序
LANGUAGES: list[tuple[str, str]] = [
    ("简体中文", "README.md"),
    ("繁體中文", "README.zh-TW.md"),
    ("English", "README.en.md"),
    ("日本語", "README.ja.md"),
    ("한국어", "README.ko.md"),
    ("Español", "README.es.md"),
    ("Français", "README.fr.md"),
    ("Deutsch", "README.de.md"),
    ("Русский", "README.ru.md"),
    ("Português (BR)", "README.pt-BR.md"),
]


def language_bar(current: str) -> str:
    """生成一行语言切换栏；当前语言加粗，其余为相对链接。"""
    parts = [
        f"**{label}**" if filename == current else f"[{label}]({filename})"
        for label, filename in LANGUAGES
    ]
    return " · ".join(parts)
