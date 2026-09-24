import secrets
from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SIDE = 1600  # обложке и полному кадру больше не нужно, а вес и LCP заметно лучше
THUMB_SIDE = 640  # превью в сетке галереи: ячейка ~350 px, запас на retina


class InvalidImage(Exception):
    pass


def unique_basename(prefix: str) -> str:
    """Имя файла со случайным хвостом. Заменённая картинка получает новый
    URL — иначе браузер неделю показывал бы старую из кэша (nginx: expires 7d).
    """
    return f"{prefix}-{secrets.token_hex(4)}"


def open_image(uploaded) -> Image.Image:
    """Открывает загрузку и приводит её к виду, пригодному для WebP.

    Заодно отсекает файлы, которые лишь притворяются изображениями.
    """
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise InvalidImage("Файл больше 5 МБ")

    try:
        image = Image.open(uploaded)
        image.load()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise InvalidImage("Не похоже на изображение") from exc

    # EXIF дальше выбрасывается, поэтому поворот фото с телефона применяем
    # к самим пикселям — иначе кадр ляжет на бок.
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        has_alpha = image.mode in ("LA", "PA") or "transparency" in image.info
        image = image.convert("RGBA" if has_alpha else "RGB")
    return image


def to_webp(image: Image.Image, basename: str, max_side: int) -> ContentFile:
    """Ужимает картинку на месте и пересохраняет в WebP.

    Метаданные (включая EXIF с геолокацией) в новый файл не попадают.
    """
    image.thumbnail((max_side, max_side))
    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=82, method=4)
    return ContentFile(buffer.getvalue(), name=f"{basename}.webp")


def process_cover(uploaded, basename: str) -> ContentFile:
    return to_webp(open_image(uploaded), basename, MAX_SIDE)


def process_gallery_image(uploaded, basename: str) -> tuple[ContentFile, ContentFile]:
    """Полный кадр для просмотра и лёгкое превью для сетки."""
    image = open_image(uploaded)
    # to_webp ужимает на месте: идём от большего размера к меньшему,
    # чтобы не держать в памяти копию исходника (на VPS 1 ГБ RAM)
    full = to_webp(image, basename, MAX_SIDE)
    thumb = to_webp(image, basename, THUMB_SIDE)
    return full, thumb
