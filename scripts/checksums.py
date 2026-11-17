"""为目录中的文件生成 SHA256SUMS.txt（跨平台，避免依赖 sha256sum/shasum）。

用法::

    python scripts/checksums.py dist
    python scripts/checksums.py artifacts artifacts/SHA256SUMS.txt
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else directory / "SHA256SUMS.txt"
    if not directory.is_dir():
        print(f"目录不存在: {directory}", file=sys.stderr)
        return 1

    lines = []
    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.name == "SHA256SUMS.txt":
            continue
        lines.append(f"{sha256(path)}  {path.name}")

    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
