from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image, UnidentifiedImageError

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_SIDE = 1600  # обложке больше не нужно, а вес и LCP заметно лучше


class InvalidImage(Exception):
    pass


def process_cover(uploaded, basename: str) -> ContentFile:
    """Пересохраняет загруженную картинку в WebP.

    Побочно решает две задачи: отсекает файлы, которые лишь притворяются
    изображениями, и вычищает метаданные (включая EXIF с геолокацией).
    """
    if uploaded.size > MAX_UPLOAD_BYTES:
        raise InvalidImage("Файл больше 5 МБ")

    try:
        image = Image.open(uploaded)
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise InvalidImage("Не похоже на изображение") from exc

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE))

    buffer = BytesIO()
    image.save(buffer, format="WEBP", quality=82, method=4)
    return ContentFile(buffer.getvalue(), name=f"{basename}.webp")
