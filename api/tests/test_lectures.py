import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from content.lectures import LectureError, decode, parse_lecture, slug_from_filename
from content.models import Course, Lecture

from .test_admin import auth_client, owner  # noqa: F401 — фикстуры

TRANSCRIPT = """---
title: 'Лекция 1. Введение'
number: 1
kind: transcript
date: 2025-09-03
permission: 'согласие лектора, сообщение ВК от 2026-10-01'
quality: edited
source:
  url: https://vk.com/video-1_1
  duration: '1:28:40'
topics: [группы, подгруппы]
summary: 'Введение в курс'
---

## 1. Начало [00:01:00]

Текст с формулой $a_1$.
"""


def md(text: str = TRANSCRIPT, **replace: str) -> str:
    for old, new in replace.items():
        text = text.replace(old, new)
    return text


# --- разбор файла -------------------------------------------------------------


def test_parse_transcript() -> None:
    p = parse_lecture(TRANSCRIPT, "01-vvedenie")
    assert p.title == "Лекция 1. Введение"
    assert p.number == 1
    assert p.date.isoformat() == "2025-09-03"
    assert p.source_duration == "1:28:40"
    assert p.topics == ["группы", "подгруппы"]
    assert p.body_md.startswith("## 1. Начало")
    assert p.raw == TRANSCRIPT


def test_decode_strips_bom_and_crlf() -> None:
    assert decode("\ufeff---\r\nx\r\n".encode()) == "---\nx\n"
    with pytest.raises(LectureError, match="UTF-8"):
        decode("лекция".encode("cp1251"))


def test_transcript_needs_permission_and_source() -> None:
    text = md(
        **{
            "permission: 'согласие лектора, сообщение ВК от 2026-10-01'\n": "",
            "source:\n  url: https://vk.com/video-1_1\n  duration: '1:28:40'\n": "",
        }
    )
    with pytest.raises(LectureError) as exc:
        parse_lecture(text, "x")
    joined = " ".join(exc.value.errors)
    assert "permission" in joined and "source.url" in joined


def test_notes_need_author_not_permission() -> None:
    notes = md(**{"kind: transcript": "kind: notes"}).replace(
        "permission: 'согласие лектора, сообщение ВК от 2026-10-01'\n", ""
    )
    with pytest.raises(LectureError, match="author"):
        parse_lecture(notes, "x")
    assert parse_lecture(notes.replace("kind: notes", "kind: notes\nauthor: Я"), "x").author == "Я"


@pytest.mark.parametrize(
    ("old", "new", "field"),
    [
        ("kind: transcript", "kind: lecture", "kind"),
        ("date: 2025-09-03", "date: 03.09.2025", "date"),
        ("quality: edited", "quality: good", "quality"),
        ("number: 1", "number: один", "number"),
        ("number: 1", "number: -1", "number"),
        ("duration: '1:28:40'", "duration: полтора часа", "source.duration"),
        ("topics: [группы, подгруппы]", "topics: группы", "topics"),
        ("quality: edited", "quality: edited\nlicense: MIT", "license"),
    ],
)
def test_rejects_bad_fields(old: str, new: str, field: str) -> None:
    with pytest.raises(LectureError) as exc:
        parse_lecture(md(**{old: new}), "x")
    assert any(f"«{field}»" in e for e in exc.value.errors), exc.value.errors


def test_reports_all_errors_at_once() -> None:
    text = md(**{"kind: transcript": "kind: x", "quality: edited": "quality: y"})
    with pytest.raises(LectureError) as exc:
        parse_lecture(text, "x")
    assert len(exc.value.errors) == 2


def test_requires_frontmatter() -> None:
    with pytest.raises(LectureError, match="шапки"):
        parse_lecture("просто текст", "x")


@pytest.mark.parametrize("name", ["Лекция 1.md", "lecture.txt", "a_b.md", "-a.md"])
def test_bad_filenames(name: str) -> None:
    with pytest.raises(LectureError):
        slug_from_filename(name)


def test_filename_with_path() -> None:
    assert slug_from_filename("C:\\lectures\\03-gruppy.md") == "03-gruppy"


# --- API ----------------------------------------------------------------------


@pytest.fixture
def course(db) -> Course:
    return Course.objects.create(
        slug="algebra",
        title="Алгебра",
        description="Курс алгебры",
        lecturer="Иванов И. И.",
        license="CC-BY-SA-4.0",
        is_published=True,
    )


def upload(client: Client, course: Course, text: str = TRANSCRIPT, name: str = "01-vvedenie.md"):
    file = SimpleUploadedFile(name, text.encode(), content_type="text/markdown")
    return client.post(f"/api/admin/courses/{course.pk}/lectures", {"file": file})


@pytest.mark.django_db
def test_upload_requires_auth(client: Client, course: Course) -> None:
    assert upload(client, course).status_code == 401


@pytest.mark.django_db
def test_upload_creates_then_replaces(auth_client: Client, course: Course) -> None:  # noqa: F811
    first = upload(auth_client, course)
    assert first.status_code == 201, first.content
    assert first.json()["lecture"]["is_published"] is False

    lecture = Lecture.objects.get()
    lecture.is_published = True
    lecture.save()

    again = upload(auth_client, course, md(**{"Введение в курс": "Новое описание"}))
    assert again.status_code == 200
    lecture.refresh_from_db()
    assert lecture.summary == "Новое описание"
    assert lecture.is_published is True  # замена файла не снимает с публикации
    assert Lecture.objects.count() == 1


@pytest.mark.django_db
def test_upload_returns_all_errors(auth_client: Client, course: Course) -> None:  # noqa: F811
    response = upload(auth_client, course, md(**{"kind: transcript": "kind: x"}), "bad.md")
    assert response.status_code == 422
    assert "«kind»" in response.json()["detail"]
    assert not Lecture.objects.exists()


@pytest.mark.django_db
def test_public_hides_drafts(client: Client, auth_client: Client, course: Course) -> None:  # noqa: F811
    upload(auth_client, course)
    assert client.get("/api/lectures").json()[0]["lectures"] == []
    assert client.get("/api/lectures/algebra/01-vvedenie").status_code == 404
    # владелец видит черновик в предпросмотре
    assert auth_client.get("/api/lectures/algebra/01-vvedenie?preview=1").status_code == 200

    Lecture.objects.update(is_published=True)
    detail = client.get("/api/lectures/algebra/01-vvedenie").json()
    # пустые поля лекции берутся из курса
    assert detail["lecturer"] == "Иванов И. И."
    assert detail["author"] == "Иванов И. И."
    assert detail["license"]["id"] == "CC-BY-SA-4.0"
    assert detail["source"]["url"] == "https://vk.com/video-1_1"
    assert detail["prev"] is None and detail["next"] is None

    raw = client.get("/api/lectures/algebra/01-vvedenie/raw")
    assert raw["Content-Type"].startswith("text/markdown")
    assert raw.content.decode() == TRANSCRIPT

    [record] = client.get("/api/lectures/dataset").json()
    assert record["id"] == "algebra/01-vvedenie"
    assert record["license"] == "CC-BY-SA-4.0"
    assert record["text"].startswith("## 1. Начало")


@pytest.mark.django_db
def test_unpublished_course_hides_lectures(client: Client, course: Course) -> None:
    Lecture.objects.create(
        course=course,
        slug="x",
        title="X",
        kind="notes",
        author="Я",
        date="2025-01-01",
        quality="edited",
        summary="s",
        body_md="b",
        raw="r",
        is_published=True,
    )
    assert client.get("/api/lectures/algebra/x").status_code == 200
    Course.objects.update(is_published=False)
    assert client.get("/api/lectures").json() == []
    assert client.get("/api/lectures/algebra/x").status_code == 404
    assert client.get("/api/lectures/dataset").json() == []


@pytest.mark.django_db
def test_prev_next_by_number(client: Client, auth_client: Client, course: Course) -> None:  # noqa: F811
    upload(auth_client, course, md(**{"number: 1": "number: 2"}), "02-b.md")
    upload(auth_client, course, md(), "01-a.md")
    Lecture.objects.update(is_published=True)
    detail = client.get("/api/lectures/algebra/02-b").json()
    assert detail["prev"] == {"slug": "01-a", "title": "Лекция 1. Введение"}
    assert detail["next"] is None


@pytest.mark.django_db
def test_course_crud(auth_client: Client) -> None:  # noqa: F811
    payload = {"title": "Линейная алгебра", "description": "d", "lecturer": "Петров"}
    created = auth_client.post("/api/admin/courses", payload, content_type="application/json")
    assert created.status_code == 201
    assert created.json()["slug"] == "lineynaya-algebra"

    dup = auth_client.post("/api/admin/courses", payload, content_type="application/json")
    assert dup.status_code == 422

    bad = auth_client.post(
        "/api/admin/courses",
        {**payload, "slug": "x", "license": "MIT"},
        content_type="application/json",
    )
    assert bad.status_code == 422

    course_id = created.json()["id"]
    response = auth_client.delete(f"/api/admin/courses/{course_id}")
    assert response.status_code == 204
