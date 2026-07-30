from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import Router

from .models import Profile, Project
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
