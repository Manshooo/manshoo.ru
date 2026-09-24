import io
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.test import Client
from PIL import Image

from content.models import Project, ProjectImage

pytestmark = pytest.mark.django_db

PASSWORD = "test-pass-12345"


@pytest.fixture
def owner() -> User:
    return User.objects.create_superuser("owner", "owner@example.com", PASSWORD)


@pytest.fixture
def auth_client(owner: User) -> Client:
    """Клиент с сессией и csrf-токеном — как ведёт себя браузер админки."""
    client = Client(enforce_csrf_checks=True)
    token = client.get("/api/auth/csrf").json()["csrf_token"]
    response = client.post(
        "/api/auth/login",
        data={"username": "owner", "password": PASSWORD},
        content_type="application/json",
        headers={"x-csrftoken": token},
    )
    assert response.status_code == 200, response.content
    # Django ротирует csrf-токен при входе — старый больше не годится,
    # админка обязана перезапросить его после логина.
    client.defaults["HTTP_X_CSRFTOKEN"] = client.get("/api/auth/csrf").json()["csrf_token"]
    return client


def project_payload(**overrides) -> dict:
    payload = {
        "title": "Новый проект",
        "tagline": "Короткое описание",
        "period_start": "2026-01-01",
        "stack": ["Go"],
        "highlights": ["Фишка"],
        "links": {"repo": "https://example.com"},
    }
    payload.update(overrides)
    return payload


def test_me_requires_auth(client: Client) -> None:
    assert client.get("/api/auth/me").status_code == 401


def test_admin_list_requires_auth(client: Client) -> None:
    assert client.get("/api/admin/projects").status_code == 401


def test_login_rejects_bad_password(client: Client, owner: User) -> None:
    response = client.post(
        "/api/auth/login",
        data={"username": "owner", "password": "wrong"},
        content_type="application/json",
    )
    assert response.status_code == 401


def test_login_rate_limited(client: Client, owner: User) -> None:
    from django.core.cache import cache

    cache.clear()
    for _ in range(5):
        client.post(
            "/api/auth/login",
            data={"username": "owner", "password": "wrong"},
            content_type="application/json",
        )
    response = client.post(
        "/api/auth/login",
        data={"username": "owner", "password": PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 429
    cache.clear()


def test_mutation_without_csrf_rejected(auth_client: Client) -> None:
    before = Project.objects.count()
    response = auth_client.post(
        "/api/admin/projects",
        data=project_payload(),
        content_type="application/json",
        headers={"x-csrftoken": "wrong-token"},
    )
    # ninja отбивает такой запрос на этапе аутентификации по куке
    assert response.status_code in (401, 403)
    assert Project.objects.count() == before


def test_login_without_csrf_rejected(client: Client, owner: User) -> None:
    strict = Client(enforce_csrf_checks=True)
    response = strict.post(
        "/api/auth/login",
        data={"username": "owner", "password": PASSWORD},
        content_type="application/json",
    )
    assert response.status_code == 403


def test_admin_sees_drafts(auth_client: Client) -> None:
    slugs = [p["slug"] for p in auth_client.get("/api/admin/projects").json()]
    assert "azzb-ru" in slugs  # черновик из сид-миграции


def test_crud_cycle(auth_client: Client) -> None:
    created = auth_client.post(
        "/api/admin/projects", data=project_payload(), content_type="application/json"
    )
    assert created.status_code == 201, created.content
    project = created.json()
    assert project["slug"] == "novyy-proekt"  # slug транслитерируется, а не остаётся кириллицей
    assert project["is_published"] is False

    # Черновик не виден публично, но виден владельцу через preview
    assert auth_client.get(f"/api/projects/{project['slug']}").status_code == 404
    assert auth_client.get(f"/api/projects/{project['slug']}?preview=1").status_code == 200

    updated = auth_client.put(
        f"/api/admin/projects/{project['id']}",
        data=project_payload(title="Новый проект", tagline="Обновлено", is_published=True),
        content_type="application/json",
    )
    assert updated.status_code == 200
    assert updated.json()["tagline"] == "Обновлено"

    # После публикации проект появляется в публичном API
    assert auth_client.get(f"/api/projects/{project['slug']}").status_code == 200

    assert auth_client.delete(f"/api/admin/projects/{project['id']}").status_code == 204
    assert not Project.objects.filter(pk=project["id"]).exists()


def test_preview_denied_for_anonymous(client: Client) -> None:
    assert client.get("/api/projects/azzb-ru?preview=1").status_code == 404


def test_slug_collision_gets_suffix(auth_client: Client) -> None:
    first = auth_client.post(
        "/api/admin/projects",
        data=project_payload(slug="dubl"),
        content_type="application/json",
    ).json()
    second = auth_client.post(
        "/api/admin/projects",
        data=project_payload(slug="dubl"),
        content_type="application/json",
    ).json()
    assert first["slug"] == "dubl"
    assert second["slug"] == "dubl-2"


def test_cover_upload_converts_to_webp(auth_client: Client) -> None:
    project = auth_client.post(
        "/api/admin/projects", data=project_payload(), content_type="application/json"
    ).json()

    buffer = io.BytesIO()
    Image.new("RGB", (2400, 1200), "navy").save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = "cover.png"

    response = auth_client.post(f"/api/admin/projects/{project['id']}/cover", data={"file": buffer})
    assert response.status_code == 200, response.content
    cover_url = response.json()["cover_url"]
    assert cover_url.endswith(".webp")

    saved = Project.objects.get(pk=project["id"]).cover
    with Image.open(saved.path) as image:
        assert image.format == "WEBP"
        assert max(image.size) <= 1600  # ужали до разумного размера
    saved.delete(save=True)


def test_cover_rejects_non_image(auth_client: Client) -> None:
    project = auth_client.post(
        "/api/admin/projects", data=project_payload(), content_type="application/json"
    ).json()

    fake = io.BytesIO(b"<?php echo 'not an image'; ?>")
    fake.name = "shell.png"
    response = auth_client.post(f"/api/admin/projects/{project['id']}/cover", data={"file": fake})
    assert response.status_code == 400


def image_file(size=(2400, 1200), name="shot.png") -> io.BytesIO:
    buffer = io.BytesIO()
    Image.new("RGB", size, "navy").save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = name
    return buffer


def create_project(client: Client, **overrides) -> dict:
    return client.post(
        "/api/admin/projects", data=project_payload(**overrides), content_type="application/json"
    ).json()


def test_cover_reupload_changes_url(auth_client: Client) -> None:
    """nginx кэширует медиа на неделю: новая обложка обязана жить по новому адресу."""
    project = create_project(auth_client)
    url = f"/api/admin/projects/{project['id']}/cover"

    first = auth_client.post(url, data={"file": image_file()}).json()["cover_url"]
    old_path = Project.objects.get(pk=project["id"]).cover.path
    second = auth_client.post(url, data={"file": image_file()}).json()["cover_url"]

    assert first != second
    assert not Path(old_path).exists()  # старый файл убран, а не брошен мусором


def test_media_urls_use_public_api_url(auth_client: Client, settings) -> None:
    """SSR ходит в api по docker-сети: ссылка на картинку не должна вести на api:8000."""
    settings.PUBLIC_API_URL = "https://api.example.com"
    settings.ALLOWED_HOSTS = ["api", "testserver"]  # как в проде: api — внутренний хост
    project = create_project(auth_client, is_published=True)
    auth_client.post(f"/api/admin/projects/{project['id']}/cover", data={"file": image_file()})
    auth_client.post(f"/api/admin/projects/{project['id']}/images", data={"file": image_file()})

    ssr = Client(headers={"host": "api:8000"})
    detail = ssr.get(f"/api/projects/{project['slug']}").json()
    card = ssr.get("/api/projects").json()
    assert detail["cover_url"].startswith("https://api.example.com/media/covers/")
    assert detail["images"][0]["url"].startswith("https://api.example.com/media/gallery/")
    assert any(c["cover_url"] == detail["cover_url"] for c in card)


def test_gallery_upload(auth_client: Client) -> None:
    project = create_project(auth_client, is_published=True)
    url = f"/api/admin/projects/{project['id']}/images"

    first = auth_client.post(url, data={"file": image_file((2400, 1200))})
    assert first.status_code == 201, first.content
    image = first.json()
    assert image["url"].endswith(".webp")
    assert image["thumb_url"].endswith(".webp")
    assert (image["width"], image["height"]) == (1600, 800)  # ужат, пропорции сохранены

    saved = ProjectImage.objects.get(pk=image["id"])
    with Image.open(saved.thumb.path) as thumb:
        assert thumb.format == "WEBP"
        assert max(thumb.size) <= 640

    second = auth_client.post(url, data={"file": image_file((800, 1000))}).json()
    # новые кадры встают в конец, публичная страница видит галерею в том же порядке
    public = auth_client.get(f"/api/projects/{project['slug']}").json()
    assert [i["id"] for i in public["images"]] == [image["id"], second["id"]]


def test_gallery_rejects_non_image(auth_client: Client) -> None:
    project = create_project(auth_client)
    fake = io.BytesIO(b"<?php echo 'not an image'; ?>")
    fake.name = "shell.png"
    response = auth_client.post(f"/api/admin/projects/{project['id']}/images", data={"file": fake})
    assert response.status_code == 400
    assert not ProjectImage.objects.exists()


def test_gallery_requires_auth(client: Client) -> None:
    project = Project.objects.get(slug="manshoo-ru")
    response = client.post(f"/api/admin/projects/{project.pk}/images", data={"file": image_file()})
    assert response.status_code == 401


def test_gallery_caption_and_order(auth_client: Client) -> None:
    project = create_project(auth_client)
    base = f"/api/admin/projects/{project['id']}/images"
    ids = [auth_client.post(base, data={"file": image_file()}).json()["id"] for _ in range(3)]

    caption = auth_client.put(
        f"{base}/{ids[1]}", data={"caption": "  Экран входа "}, content_type="application/json"
    )
    assert caption.json()["caption"] == "Экран входа"

    reordered = auth_client.put(
        f"{base}/order", data={"ids": ids[::-1]}, content_type="application/json"
    )
    assert [i["id"] for i in reordered.json()] == ids[::-1]
    detail = auth_client.get(f"/api/admin/projects/{project['id']}").json()
    assert [i["id"] for i in detail["images"]] == ids[::-1]

    # неполный список — значит, галерею правили в другой вкладке
    stale = auth_client.put(f"{base}/order", data={"ids": ids[:2]}, content_type="application/json")
    assert stale.status_code == 409


def test_gallery_image_belongs_to_project(auth_client: Client) -> None:
    owner_project = create_project(auth_client)
    other = create_project(auth_client, title="Другой")
    image = auth_client.post(
        f"/api/admin/projects/{owner_project['id']}/images", data={"file": image_file()}
    ).json()
    response = auth_client.delete(f"/api/admin/projects/{other['id']}/images/{image['id']}")
    assert response.status_code == 404


def test_gallery_files_removed_with_image_and_project(auth_client: Client) -> None:
    project = create_project(auth_client)
    base = f"/api/admin/projects/{project['id']}/images"
    first = auth_client.post(base, data={"file": image_file()}).json()
    auth_client.post(base, data={"file": image_file()})
    auth_client.post(f"/api/admin/projects/{project['id']}/cover", data={"file": image_file()})

    saved = ProjectImage.objects.get(pk=first["id"])
    paths = [Path(saved.image.path), Path(saved.thumb.path)]
    assert auth_client.delete(f"{base}/{first['id']}").status_code == 204
    assert not any(p.exists() for p in paths)

    # удаление проекта каскадом забирает оставшиеся кадры и обложку
    leftovers = [Path(f.path) for i in ProjectImage.objects.all() for f in (i.image, i.thumb)]
    leftovers.append(Path(Project.objects.get(pk=project["id"]).cover.path))
    assert auth_client.delete(f"/api/admin/projects/{project['id']}").status_code == 204
    assert not any(p.exists() for p in leftovers)


def test_profile_update(auth_client: Client) -> None:
    response = auth_client.put(
        "/api/admin/profile",
        data={
            "name": "Yanislav Pichugin",
            "headline": "Новый заголовок",
            "skills": ["Go", "Svelte"],
            "socials": {"github": "https://github.com/Manshooo"},
        },
        content_type="application/json",
    )
    assert response.status_code == 200
    assert response.json()["headline"] == "Новый заголовок"
    assert auth_client.get("/api/profile").json()["headline"] == "Новый заголовок"


def test_logout(auth_client: Client) -> None:
    assert auth_client.post("/api/auth/logout").status_code == 200
    assert auth_client.get("/api/auth/me").status_code == 401
