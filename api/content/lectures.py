"""Разбор .md-файла лекции: YAML-шапка + Markdown-тело (схема — docs/09-lectures.md).

Админка загружает файл как есть; здесь он проверяется целиком, и владелец
получает список всех ошибок сразу, а не по одной за попытку.
"""

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any

import yaml

LICENSES = {
    "CC-BY-4.0": ("CC BY 4.0", "https://creativecommons.org/licenses/by/4.0/deed.ru"),
    "CC-BY-SA-4.0": ("CC BY-SA 4.0", "https://creativecommons.org/licenses/by-sa/4.0/deed.ru"),
    "CC-BY-NC-4.0": ("CC BY-NC 4.0", "https://creativecommons.org/licenses/by-nc/4.0/deed.ru"),
    "CC0-1.0": ("CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/deed.ru"),
}
KINDS = ("transcript", "notes")
QUALITIES = ("asr", "edited", "verified")

MAX_SIZE = 2 * 1024 * 1024  # самая длинная лекция в тексте — сотни КБ
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DURATION = re.compile(r"^(?:\d+:)?\d{1,2}:\d{2}$")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)


class LectureError(ValueError):
    def __init__(self, errors: list[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass
class ParsedLecture:
    """Поля модели Lecture. Пустые lecturer/language/license наследуются от курса."""

    slug: str
    title: str
    kind: str
    date: dt.date
    quality: str
    summary: str
    body_md: str
    raw: str
    number: int | None = None
    lecturer: str = ""
    author: str = ""
    updated: dt.date | None = None
    language: str = ""
    license: str = ""
    permission: str = ""
    source_url: str = ""
    source_title: str = ""
    source_duration: str = ""
    topics: list[str] = field(default_factory=list)


def decode(data: bytes) -> str:
    if len(data) > MAX_SIZE:
        raise LectureError([f"файл больше {MAX_SIZE // 1024 // 1024} МБ"])
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise LectureError(["файл не в кодировке UTF-8"]) from exc
    return text.replace("\r\n", "\n")


def slug_from_filename(filename: str) -> str:
    name = filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    if not name.lower().endswith(".md"):
        raise LectureError([f"«{name}»: нужен файл .md"])
    slug = name[:-3]
    if not SLUG.match(slug):
        raise LectureError(
            [f"«{name}»: имя файла станет адресом страницы — только a-z, 0-9 и дефис"]
        )
    return slug


class _Fields:
    """Читает поля шапки и копит ошибки, чтобы показать их все разом."""

    def __init__(self, data: dict[str, Any], errors: list[str], prefix: str = ""):
        self.data, self.errors, self.prefix = data, errors, prefix

    def err(self, key: str, message: str) -> None:
        self.errors.append(f"«{self.prefix}{key}»: {message}")

    def text(self, key: str, required: bool = False) -> str:
        value = self.data.get(key)
        if value is None or value == "":
            if required:
                self.err(key, "обязательное поле")
            return ""
        # YAML читает 2025 и 3 как числа — для текстовых полей это не ошибка
        if isinstance(value, int | float) and not isinstance(value, bool):
            return str(value)
        if not isinstance(value, str):
            self.err(key, "должно быть строкой")
            return ""
        return value.strip()

    def date(self, key: str, required: bool = False) -> dt.date | None:
        value = self.data.get(key)
        if value is None or value == "":
            if required:
                self.err(key, "обязательное поле, формат ГГГГ-ММ-ДД")
            return None
        if isinstance(value, dt.datetime):
            return value.date()
        if isinstance(value, dt.date):
            return value
        try:
            return dt.date.fromisoformat(str(value))
        except ValueError:
            self.err(key, "дата в формате ГГГГ-ММ-ДД")
            return None

    def choice(self, key: str, allowed: tuple[str, ...] | dict, required: bool = True) -> str:
        value = self.text(key, required=required)
        if value and value not in allowed:
            self.err(key, f"одно из: {', '.join(allowed)}")
            return ""
        return value

    def strings(self, key: str) -> list[str]:
        value = self.data.get(key)
        if value is None:
            return []
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            self.err(key, "список строк, например [теория групп, подгруппы]")
            return []
        return [v.strip() for v in value if v.strip()]


def parse_lecture(text: str, slug: str) -> ParsedLecture:
    match = FRONTMATTER.match(text)
    if not match:
        raise LectureError(["нет YAML-шапки: файл должен начинаться со строки ---"])
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise LectureError([f"шапка не разбирается как YAML: {exc}"]) from exc
    if not isinstance(data, dict):
        raise LectureError(["шапка должна быть набором полей «ключ: значение»"])

    errors: list[str] = []
    f = _Fields(data, errors)
    body = text[match.end() :].strip() + "\n"
    if len(body.strip()) == 0:
        errors.append("после шапки нет текста")

    kind = f.choice("kind", KINDS)
    number = data.get("number")
    if number is not None and (
        not isinstance(number, int) or isinstance(number, bool) or number < 0
    ):
        f.err("number", "целое неотрицательное число")
        number = None

    source_url = source_title = source_duration = ""
    source = data.get("source")
    if source is not None:
        if not isinstance(source, dict):
            f.err("source", "объект с полями url, title, duration")
        else:
            s = _Fields(source, errors, prefix="source.")
            source_url = s.text("url", required=True)
            if source_url and not re.match(r"^https?://", source_url):
                s.err("url", "ссылка http(s)")
            source_title = s.text("title")
            source_duration = s.text("duration")
            if source_duration and not DURATION.match(source_duration):
                s.err("duration", "Ч:ММ:СС или ММ:СС, в кавычках: '1:28:40'")

    permission = f.text("permission")
    author = f.text("author")
    if kind == "transcript":
        # Транскрипция воспроизводит чужое произведение целиком: без разрешения
        # автора её не публикуем (docs/09-lectures.md, «Права»).
        if not permission:
            f.err("permission", "у транскрипции обязательно: где и как получено согласие автора")
        if not source_url:
            f.err("source.url", "у транскрипции обязательна ссылка на оригинал")
    elif kind == "notes" and not author:
        f.err("author", "у конспекта обязательно: кто составил")

    parsed = ParsedLecture(
        slug=slug,
        title=f.text("title", required=True),
        kind=kind,
        date=f.date("date", required=True),  # type: ignore[arg-type]
        quality=f.choice("quality", QUALITIES),
        summary=f.text("summary", required=True),
        body_md=body,
        raw=text,
        number=number,
        lecturer=f.text("lecturer"),
        author=author,
        updated=f.date("updated"),
        language=f.text("language"),
        license=f.choice("license", LICENSES, required=False),
        permission=permission,
        source_url=source_url,
        source_title=source_title,
        source_duration=source_duration,
        topics=f.strings("topics"),
    )
    if errors:
        raise LectureError(errors)
    return parsed
