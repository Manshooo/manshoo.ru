import io

import pytest
from django.contrib.auth.models import User
from django.test import Client
from PIL import Image

from content.models import Project

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
