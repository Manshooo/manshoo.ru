import io

import pytest
from django.test import Client
from PIL import Image

from content.models import Project
from content.og import og_cache_path, render_og

pytestmark = pytest.mark.django_db


def test_og_endpoint_returns_png(client: Client) -> None:
    response = client.get("/api/projects/manshoo-ru/og.png")
    assert response.status_code == 200
    assert response["Content-Type"] == "image/png"

    image = Image.open(io.BytesIO(b"".join(response.streaming_content)))
    assert image.size == (1200, 630)


def test_og_cached_and_reused(client: Client) -> None:
    project = Project.objects.get(slug="manshoo-ru")
    version = str(int(project.updated_at.timestamp()))
    path = og_cache_path(project.slug, version)

    assert not path.exists()
    client.get("/api/projects/manshoo-ru/og.png")
    assert path.exists()

    mtime = path.stat().st_mtime
    client.get("/api/projects/manshoo-ru/og.png")
    assert path.stat().st_mtime == mtime  # второй запрос не перерисовывает


def test_og_draft_hidden(client: Client) -> None:
    assert client.get("/api/projects/azzb-ru/og.png").status_code == 404


def test_render_handles_long_text() -> None:
    image = render_og(
        title="Очень длинное название проекта, которое не влезает в одну строку никак",
        tagline="И подзаголовок тоже длинный, с описанием сути проекта в подробностях",
        stack=["Python", "Django", "Go", "SvelteKit", "PostgreSQL", "Docker", "nginx"],
        author="Янислав Пичугин",
    )
    assert image.size == (1200, 630)
