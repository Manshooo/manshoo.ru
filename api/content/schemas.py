from datetime import date, datetime

from django.http import HttpRequest
from ninja import Schema

from .models import Profile, Project


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
        if not obj.photo:
            return None
        request: HttpRequest = context["request"]
        return request.build_absolute_uri(obj.photo.url)


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
        if not obj.cover:
            return None
        request: HttpRequest = context["request"]
        return request.build_absolute_uri(obj.cover.url)


class ProjectDetailOut(ProjectCardOut):
    id: int
    description_md: str
    highlights: list[str]
    links: dict[str, str]
    is_published: bool
    sort_order: int


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
