"""Генерация og:image — картинки-превью ссылки в мессенджерах и соцсетях.

Рисуем сами (Pillow), а не берём обложку проекта: в превью важнее читаемый
заголовок, чем скриншот. Результат кэшируется на диске и переживает
рестарт; ключ кэша включает время правки проекта, поэтому после
редактирования картинка перерисовывается сама.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from django.conf import settings
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1200, 630
MARGIN = 80

BG = (15, 17, 22)
FG = (231, 233, 238)
MUTED = (152, 161, 176)
ACCENT = (130, 167, 255)

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
FONT_BOLD = FONT_DIR / "DejaVuSans-Bold.ttf"
FONT_REGULAR = FONT_DIR / "DejaVuSans.ttf"


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        # Без шрифта в системе Pillow нарисует встроенным — некрасиво,
        # но лучше, чем 500 на превью ссылки.
        return ImageFont.load_default()


def og_cache_path(slug: str, version: str) -> Path:
    return Path(settings.MEDIA_ROOT) / "og" / f"{slug}-{version}.png"


def render_og(title: str, tagline: str, stack: list[str], author: str) -> Image.Image:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    # Акцентная полоса слева — узнаваемая рамка вместо пустого поля
    draw.rectangle((0, 0, 12, HEIGHT), fill=ACCENT)

    title_font = _font(FONT_BOLD, 64)
    tagline_font = _font(FONT_REGULAR, 34)
    meta_font = _font(FONT_REGULAR, 28)

    y = MARGIN
    for line in textwrap.wrap(title, width=26)[:3]:
        draw.text((MARGIN, y), line, font=title_font, fill=FG)
        y += 78

    y += 12
    for line in textwrap.wrap(tagline, width=52)[:3]:
        draw.text((MARGIN, y), line, font=tagline_font, fill=MUTED)
        y += 46

    if stack:
        stack_line = " · ".join(stack[:6])
        draw.text((MARGIN, HEIGHT - MARGIN - 70), stack_line, font=meta_font, fill=ACCENT)

    draw.text((MARGIN, HEIGHT - MARGIN - 20), author, font=meta_font, fill=MUTED)
    return image


def get_or_create_og(project, author: str) -> Path:
    """Путь к картинке проекта; рисует и кэширует при первом обращении."""
    version = str(int(project.updated_at.timestamp()))
    path = og_cache_path(project.slug, version)
    if path.exists():
        return path

    path.parent.mkdir(parents=True, exist_ok=True)
    image = render_og(project.title, project.tagline, project.stack, author)
    image.save(path, format="PNG", optimize=True)

    # Старые версии этого же проекта больше не нужны
    for stale in path.parent.glob(f"{project.slug}-*.png"):
        if stale != path:
            stale.unlink(missing_ok=True)
    return path
