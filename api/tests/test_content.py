import pytest
from django.test import Client

from content.models import Project

pytestmark = pytest.mark.django_db


def test_profile_seeded(client: Client) -> None:
    response = client.get("/api/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Yanislav Pichugin"
    assert "github" in data["socials"]


def test_projects_only_published(client: Client) -> None:
    response = client.get("/api/projects")
    assert response.status_code == 200
    slugs = [p["slug"] for p in response.json()]
    assert "manshoo-ru" in slugs
    # azzb-ru засеян черновиком и не должен быть виден
    assert "azzb-ru" not in slugs
    assert Project.objects.filter(slug="azzb-ru", is_published=False).exists()


def test_project_detail(client: Client) -> None:
    response = client.get("/api/projects/manshoo-ru")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "manshoo.ru"
    assert isinstance(data["highlights"], list) and data["highlights"]
    assert data["links"]["repo"].startswith("https://github.com/")


def test_project_draft_hidden(client: Client) -> None:
    assert client.get("/api/projects/azzb-ru").status_code == 404


def test_project_unknown_404(client: Client) -> None:
    assert client.get("/api/projects/nope").status_code == 404
