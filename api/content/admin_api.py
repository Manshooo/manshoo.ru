from django.db.models import Max
from django.http import HttpRequest
from django.shortcuts import get_object_or_404
from ninja import File, Router, Status
from ninja.errors import HttpError
from ninja.files import UploadedFile
from ninja.security import django_auth

from .images import InvalidImage, process_cover, process_gallery_image, unique_basename
from .models import Profile, Project, ProjectImage
from .schemas import (
    ImageOrderIn,
    ProfileIn,
    ProfileOut,
    ProjectDetailOut,
    ProjectImageIn,
    ProjectImageOut,
    ProjectIn,
)
from .slugs import make_slug

router = Router(tags=["admin"], auth=django_auth)


@router.get("/projects", response=list[ProjectDetailOut])
def list_projects(request: HttpRequest):
    """Все проекты, включая черновики (в отличие от публичного списка)."""
    return Project.objects.prefetch_related("images")


@router.get("/projects/{int:project_id}", response=ProjectDetailOut)
def get_project(request: HttpRequest, project_id: int):
    return get_object_or_404(Project, pk=project_id)


@router.post("/projects", response={201: ProjectDetailOut})
def create_project(request: HttpRequest, data: ProjectIn):
    payload = data.dict()
    payload["slug"] = unique_slug(payload["slug"] or payload["title"])
    return Status(201, Project.objects.create(**payload))


@router.put("/projects/{int:project_id}", response=ProjectDetailOut)
def update_project(request: HttpRequest, project_id: int, data: ProjectIn):
    project = get_object_or_404(Project, pk=project_id)
    payload = data.dict()
    payload["slug"] = unique_slug(payload["slug"] or payload["title"], exclude_pk=project.pk)
    for field, value in payload.items():
        setattr(project, field, value)
    project.save()
    return project


@router.delete("/projects/{int:project_id}", response={204: None})
def delete_project(request: HttpRequest, project_id: int):
    get_object_or_404(Project, pk=project_id).delete()
    return Status(204, None)


@router.post("/projects/{int:project_id}/cover", response=ProjectDetailOut)
def upload_cover(
    request: HttpRequest,
    project_id: int,
    file: UploadedFile = File(...),  # noqa: B008 — идиома django-ninja для multipart
):
    project = get_object_or_404(Project, pk=project_id)
    try:
        processed = process_cover(file, basename=unique_basename(project.slug))
    except InvalidImage as exc:
        raise HttpError(400, str(exc)) from exc

    project.cover.delete(save=False)  # старый файл не оставляем мусором
    project.cover.save(processed.name, processed, save=True)
    return project


@router.delete("/projects/{int:project_id}/cover", response=ProjectDetailOut)
def delete_cover(request: HttpRequest, project_id: int):
    project = get_object_or_404(Project, pk=project_id)
    project.cover.delete(save=True)
    return project


@router.post("/projects/{int:project_id}/images", response={201: ProjectImageOut})
def upload_image(
    request: HttpRequest,
    project_id: int,
    file: UploadedFile = File(...),  # noqa: B008 — идиома django-ninja для multipart
):
    """Добавляет кадр в конец галереи. Несколько файлов админка шлёт по одному:
    так каждый укладывается в лимиты загрузки, а ошибка не губит остальные."""
    project = get_object_or_404(Project, pk=project_id)
    try:
        full, thumb = process_gallery_image(file, basename=unique_basename(project.slug))
    except InvalidImage as exc:
        raise HttpError(400, str(exc)) from exc

    last = project.images.aggregate(last=Max("sort_order"))["last"]
    image = ProjectImage.objects.create(
        project=project,
        image=full,
        thumb=thumb,
        sort_order=0 if last is None else last + 1,
    )
    return Status(201, image)


@router.put("/projects/{int:project_id}/images/order", response=list[ProjectImageOut])
def reorder_images(request: HttpRequest, project_id: int, data: ImageOrderIn):
    project = get_object_or_404(Project, pk=project_id)
    images = {image.pk: image for image in project.images.all()}
    # Порядок принимаем только для галереи целиком: если кадры успели
    # добавить или удалить в другой вкладке, молча терять их нельзя
    if sorted(data.ids) != sorted(images):
        raise HttpError(409, "Галерея изменилась — обновите страницу")

    for position, image_id in enumerate(data.ids):
        images[image_id].sort_order = position
    ProjectImage.objects.bulk_update(images.values(), ["sort_order"])
    return [images[image_id] for image_id in data.ids]


@router.put("/projects/{int:project_id}/images/{int:image_id}", response=ProjectImageOut)
def update_image(request: HttpRequest, project_id: int, image_id: int, data: ProjectImageIn):
    image = get_object_or_404(ProjectImage, pk=image_id, project_id=project_id)
    image.caption = data.caption.strip()
    image.save(update_fields=["caption"])
    return image


@router.delete("/projects/{int:project_id}/images/{int:image_id}", response={204: None})
def delete_image(request: HttpRequest, project_id: int, image_id: int):
    # файлы с диска убирает сигнал post_delete (content/models.py)
    get_object_or_404(ProjectImage, pk=image_id, project_id=project_id).delete()
    return Status(204, None)


@router.put("/profile", response=ProfileOut)
def update_profile(request: HttpRequest, data: ProfileIn):
    profile = Profile.load()
    for field, value in data.dict().items():
        setattr(profile, field, value)
    profile.save()
    return profile


def unique_slug(source: str, exclude_pk: int | None = None) -> str:
    """Уникальный латинский slug; при совпадении добавляет -2, -3 и т.д."""
    base = make_slug(source)
    if not base:
        raise HttpError(422, "Не удалось построить slug — задайте его вручную")

    candidate, counter = base, 2
    while True:
        taken = Project.objects.filter(slug=candidate)
        if exclude_pk:
            taken = taken.exclude(pk=exclude_pk)
        if not taken.exists():
            return candidate
        candidate = f"{base}-{counter}"
        counter += 1
