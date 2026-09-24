from datetime import date, datetime

from django.conf import settings
from django.db.models.fields.files import FieldFile
from django.http import HttpRequest
from ninja import Field, Schema

from .models import Profile, Project, ProjectImage


def media_url(file: FieldFile, request: HttpRequest) -> str | None:
    """Абсолютная ссылка на загрузку — такая, что откроется в браузере.

    Хост запроса годится не всегда: SSR спрашивает api по внутреннему
    адресу, поэтому основой служит публичный адрес из настроек.
    """
    if not file:
        return None
    if settings.PUBLIC_API_URL:
        return f"{settings.PUBLIC_API_URL}{file.url}"
    return request.build_absolute_uri(file.url)


class ProfileOut(Schema):
    name: str
    headline: str
    bio_md: str
    location: str
    skills: list[str]
    socials: dict[str, str]
    meta_description: str
    photo_url: str | None = None

    @staticmethod
    def resolve_photo_url(obj: Profile, context) -> str | None:
        return media_url(obj.photo, context["request"])


class ProfileIn(Schema):
    name: str
    headline: str
    bio_md: str = ""
    location: str = ""
    skills: list[str] = []
    socials: dict[str, str] = {}
    meta_description: str = ""


class ProjectCardOut(Schema):
    slug: str
    title: str
    tagline: str
    role: str
    org: str
    project_type: str
    status: str
    period_start: date
    period_end: date | None
    stack: list[str]
    is_featured: bool
    uptime_monitor_slug: str
    cover_url: str | None = None
    updated_at: datetime

    @staticmethod
    def resolve_cover_url(obj: Project, context) -> str | None:
        return media_url(obj.cover, context["request"])


class ProjectImageOut(Schema):
    id: int
    url: str
    thumb_url: str
    width: int
    height: int
    caption: str

    @staticmethod
    def resolve_url(obj: ProjectImage, context) -> str | None:
        return media_url(obj.image, context["request"])

    @staticmethod
    def resolve_thumb_url(obj: ProjectImage, context) -> str | None:
        return media_url(obj.thumb, context["request"])


class ProjectDetailOut(ProjectCardOut):
    id: int
    description_md: str
    highlights: list[str]
    links: dict[str, str]
    is_published: bool
    sort_order: int
    images: list[ProjectImageOut]


class ProjectIn(Schema):
    """Вход формы админки. slug можно не присылать — соберётся из title."""

    title: str
    tagline: str
    slug: str = ""
    description_md: str = ""
    role: str = ""
    org: str = ""
    project_type: str = Project.Type.PET
    status: str = Project.Status.ACTIVE
    period_start: date
    period_end: date | None = None
    stack: list[str] = []
    highlights: list[str] = []
    links: dict[str, str] = {}
    is_published: bool = False
    is_featured: bool = False
    sort_order: int = 0
    uptime_monitor_slug: str = ""


class ProjectImageIn(Schema):
    caption: str = Field("", max_length=200)


class ImageOrderIn(Schema):
    """Галерея целиком, id кадров в нужном порядке."""

    ids: list[int]
