from django.test import Client, override_settings


def test_healthz(client: Client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_ping(client: Client) -> None:
    response = client.get("/api/ping")
    assert response.status_code == 200
    assert response.json() == {"ping": "pong"}


def test_django_admin_hidden_when_disabled(client: Client, urlconf_reloader) -> None:
    """Запасная админка исчезает с ENABLE_DJANGO_ADMIN=0 (значение прода).

    В dev-контейнере DEBUG=1, поэтому проверяем не текущее окружение,
    а сам переключатель: перечитываем urlconf с выключенным флагом.
    """
    with override_settings(ENABLE_DJANGO_ADMIN=False):
        urlconf_reloader()
        assert client.get("/django-admin/").status_code == 404

    with override_settings(ENABLE_DJANGO_ADMIN=True):
        urlconf_reloader()
        # включённая админка редиректит на свою форму входа
        assert client.get("/django-admin/").status_code == 302
