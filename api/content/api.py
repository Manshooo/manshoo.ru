from django.http import FileResponse, HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Profile, Project
from .og import get_or_create_og
from .schemas import ProfileOut, ProjectCardOut, ProjectDetailOut

router = Router(tags=["content"])


@router.get("/profile", response=ProfileOut)
def profile(request: HttpRequest) -> Profile:
    return Profile.load()


@router.get("/projects", response=list[ProjectCardOut])
def projects(request: HttpRequest):
    return Project.objects.filter(is_published=True)


@router.get("/projects/{slug}", response=ProjectDetailOut)
def project(request: HttpRequest, slug: str, preview: bool = False) -> Project:
    """preview=1 отдаёт черновик — но только владельцу с активной сессией."""
    if preview and request.user.is_authenticated:
        return get_object_or_404(Project, slug=slug)
    return get_object_or_404(Project, slug=slug, is_published=True)


@router.get("/projects/{slug}/og.png", include_in_schema=False)
def project_og(request: HttpRequest, slug: str):
    """Картинка превью ссылки. Рисуется один раз и кэшируется на диске."""
    obj = get_object_or_404(Project, slug=slug, is_published=True)
    path = get_or_create_og(obj, author=Profile.load().name)
    response = FileResponse(path.open("rb"), content_type="image/png")
    response["Cache-Control"] = "public, max-age=86400"
    return response
