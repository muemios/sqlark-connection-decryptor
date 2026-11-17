"""生成项目图标 assets/sqlark.ico（需要 Pillow）。"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SIZE = 256


def build_icon() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 圆角深蓝底
    draw.rounded_rectangle([8, 8, SIZE - 8, SIZE - 8], radius=52, fill=(24, 48, 92, 255))

    # 数据库圆柱
    body = (70, 130, 220, 255)
    draw.ellipse([52, 52, 204, 96], fill=body)
    draw.rectangle([52, 74, 204, 158], fill=body)
    draw.ellipse([52, 136, 204, 180], fill=(52, 104, 186, 255))
    draw.ellipse([62, 58, 194, 90], fill=(120, 176, 240, 255))

    # 锁
    draw.rounded_rectangle([150, 150, 226, 218], radius=14, fill=(255, 255, 255, 255))
    draw.arc([162, 118, 214, 178], start=180, end=360, fill=(255, 255, 255, 255), width=14)
    draw.ellipse([180, 172, 196, 188], fill=(24, 48, 92, 255))
    draw.rounded_rectangle([185, 184, 191, 202], radius=3, fill=(24, 48, 92, 255))
    return image


def main() -> int:
    target = ROOT / "assets" / "sqlark.ico"
    target.parent.mkdir(parents=True, exist_ok=True)
    build_icon().save(
        target,
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print(f"已生成图标: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
