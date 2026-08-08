import pytest

# Пустой conftest в корне api/ добавляет каталог в sys.path,
# чтобы пакеты config и content импортировались в тестах.


@pytest.fixture(autouse=True)
def media_to_tmp(settings, tmp_path):
    """Тесты с загрузками пишут во временный каталог, а не в рабочий media/."""
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def urlconf_reloader():
    """Перечитывает config.urls: маршруты собираются при импорте, поэтому
    override_settings сам по себе на них не влияет."""
    import importlib

    from django.urls import clear_url_caches

    import config.urls

    def reload_urls():
        clear_url_caches()
        importlib.reload(config.urls)

    yield reload_urls
    reload_urls()  # вернуть маршруты, соответствующие реальным настройкам
