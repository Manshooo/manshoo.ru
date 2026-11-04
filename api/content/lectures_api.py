"""Лекции: публичное чтение и админские загрузка/публикация (docs/09-lectures.md)."""

from django.db.models import Prefetch
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404
from ninja import File, Router, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.security import django_auth

from .lectures import LICENSES, LectureError, decode, parse_lecture, slug_from_filename
from .models import Course, Lecture
from .schemas import (
    CourseIn,
    CourseOut,
    DatasetRecord,
    LectureCardOut,
    LectureOut,
    LecturePatch,
    UploadResult,
)
from .slugs import make_slug

public = Router(tags=["lectures"])
admin = Router(tags=["admin"], auth=django_auth)


def license_out(license_id: str) -> dict:
    name, url = LICENSES[license_id]
    return {"id": license_id, "name": name, "url": url}


def card(lecture: Lecture) -> dict:
    return {
        "id": lecture.pk,
        "slug": lecture.slug,
        "title": lecture.title,
        "number": lecture.number,
        "kind": lecture.kind,
        "date": lecture.date,
        "updated": lecture.effective_updated,
        "summary": lecture.summary,
        "duration": lecture.source_duration,
        "is_published": lecture.is_published,
    }


def course_out(course: Course, lectures) -> dict:
    return {
        "id": course.pk,
        "slug": course.slug,
        "title": course.title,
        "description": course.description,
        "body_md": course.body_md,
        "lecturer": course.lecturer,
        "institution": course.institution,
        "year": course.year,
        "language": course.language,
        "license": license_out(course.license),
        "is_published": course.is_published,
        "sort_order": course.sort_order,
        "lectures": [card(lecture) for lecture in lectures],
    }


def published_courses():
    lectures = Lecture.objects.filter(is_published=True)
    return Course.objects.filter(is_published=True).prefetch_related(
        Prefetch("lectures", queryset=lectures, to_attr="published")
    )


# --- публичное ----------------------------------------------------------------


@public.get("", response=list[CourseOut])
def catalog(request: HttpRequest):
    """Опубликованные курсы с опубликованными лекциями (без текстов)."""
    return [course_out(c, c.published) for c in published_courses()]


@public.get("/dataset", response=list[DatasetRecord])
def dataset(request: HttpRequest):
    """Все опубликованные лекции с текстом — основа lectures/dataset.jsonl."""
    return [
        {
            "id": f"{course.slug}/{lec.slug}",
            "course": course.title,
            "title": lec.title,
            "number": lec.number,
            "kind": lec.kind,
            "lecturer": lec.effective_lecturer,
            "author": lec.effective_author,
            "institution": course.institution or None,
            "date": lec.date,
            "updated": lec.effective_updated,
            "language": lec.effective_language,
            "license": lec.effective_license,
            "quality": lec.quality,
            "source_url": lec.source_url or None,
            "topics": lec.topics,
            "summary": lec.summary,
            "text": lec.body_md,
        }
        for course in published_courses()
        for lec in course.published
    ]


def find_lecture(request: HttpRequest, course_slug: str, slug: str, preview: bool) -> Lecture:
    """preview=1 отдаёт черновик — но только владельцу с активной сессией."""
    qs = Lecture.objects.select_related("course")
    if not (preview and request.user.is_authenticated):
        qs = qs.filter(is_published=True, course__is_published=True)
    return get_object_or_404(qs, course__slug=course_slug, slug=slug)


@public.get("/{course_slug}/{slug}", response=LectureOut)
def lecture_detail(request: HttpRequest, course_slug: str, slug: str, preview: bool = False):
    lec = find_lecture(request, course_slug, slug, preview)
    course = lec.course
    siblings = list(course.lectures.filter(is_published=True).only("slug", "title", "number"))
    if lec not in siblings:  # черновик в предпросмотре: соседи — среди всех лекций
        siblings = list(course.lectures.only("slug", "title", "number"))
    i = siblings.index(lec)

    def link(other: Lecture | None):
        return {"slug": other.slug, "title": other.title} if other else None

    return {
        "slug": lec.slug,
        "title": lec.title,
        "number": lec.number,
        "kind": lec.kind,
        "lecturer": lec.effective_lecturer,
        "author": lec.effective_author,
        "date": lec.date,
        "updated": lec.effective_updated,
        "language": lec.effective_language,
        "license": license_out(lec.effective_license),
        "quality": lec.quality,
        "is_published": lec.is_published,
        "source": (
            {"url": lec.source_url, "title": lec.source_title, "duration": lec.source_duration}
            if lec.source_url
            else None
        ),
        "topics": lec.topics,
        "summary": lec.summary,
        "body_md": lec.body_md,
        "course": {
            "slug": course.slug,
            "title": course.title,
            "description": course.description,
            "lecturer": course.lecturer,
            "institution": course.institution,
            "language": course.language,
            "license": license_out(course.license),
        },
        "prev": link(siblings[i - 1] if i > 0 else None),
        "next": link(siblings[i + 1] if i + 1 < len(siblings) else None),
    }


@public.get("/{course_slug}/{slug}/raw", include_in_schema=False)
def lecture_raw(request: HttpRequest, course_slug: str, slug: str, preview: bool = False):
    """Исходный .md как загрузили: шапка с лицензией едет вместе с текстом."""
    lec = find_lecture(request, course_slug, slug, preview)
    return HttpResponse(lec.raw, content_type="text/markdown; charset=utf-8")


# --- админка ------------------------------------------------------------------


@admin.get("/courses", response=list[CourseOut])
def admin_courses(request: HttpRequest):
    """Все курсы и лекции, включая черновики."""
    return [course_out(c, c.lectures.all()) for c in Course.objects.prefetch_related("lectures")]


def apply_course(course: Course, data: CourseIn) -> Course:
    if data.license not in LICENSES:
        raise HttpError(422, f"Неизвестная лицензия, допустимы: {', '.join(LICENSES)}")
    payload = data.dict()
    slug = make_slug(payload["slug"] or payload["title"])
    if not slug:
        raise HttpError(422, "Не удалось построить slug — задайте его вручную")
    if Course.objects.filter(slug=slug).exclude(pk=course.pk).exists():
        raise HttpError(422, f"Курс с адресом «{slug}» уже есть")
    payload["slug"] = slug
    for key, value in payload.items():
        setattr(course, key, value)
    course.save()
    return course


@admin.post("/courses", response={201: CourseOut})
def create_course(request: HttpRequest, data: CourseIn):
    course = apply_course(Course(), data)
    return Status(201, course_out(course, []))


@admin.put("/courses/{int:course_id}", response=CourseOut)
def update_course(request: HttpRequest, course_id: int, data: CourseIn):
    course = apply_course(get_object_or_404(Course, pk=course_id), data)
    return course_out(course, course.lectures.all())


@admin.delete("/courses/{int:course_id}", response={204: None})
def delete_course(request: HttpRequest, course_id: int):
    get_object_or_404(Course, pk=course_id).delete()
    return Status(204, None)


@admin.post("/courses/{int:course_id}/lectures", response={200: UploadResult, 201: UploadResult})
def upload_lecture(
    request: HttpRequest,
    course_id: int,
    file: UploadedFile = File(...),  # noqa: B008 — идиома django-ninja для multipart
):
    """Загрузка .md. Файл с тем же именем заменяет лекцию; статус публикации не меняется."""
    course = get_object_or_404(Course, pk=course_id)
    try:
        slug = slug_from_filename(file.name or "")
        parsed = parse_lecture(decode(file.read()), slug)
    except LectureError as exc:
        # все ошибки файла одним ответом, по строке на ошибку
        raise HttpError(422, "\n".join(exc.errors)) from exc

    fields = vars(parsed).copy()
    fields.pop("slug")
    lecture, created = Lecture.objects.update_or_create(course=course, slug=slug, defaults=fields)
    return Status(201 if created else 200, {"created": created, "lecture": card(lecture)})


@admin.patch("/lectures/{int:lecture_id}", response=LectureCardOut)
def patch_lecture(request: HttpRequest, lecture_id: int, data: LecturePatch):
    lecture = get_object_or_404(Lecture, pk=lecture_id)
    lecture.is_published = data.is_published
    lecture.save(update_fields=["is_published", "updated_at"])
    return card(lecture)


@admin.delete("/lectures/{int:lecture_id}", response={204: None})
def delete_lecture(request: HttpRequest, lecture_id: int):
    get_object_or_404(Lecture, pk=lecture_id).delete()
    return Status(204, None)
