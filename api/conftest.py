import pytest

# Пустой conftest в корне api/ добавляет каталог в sys.path,
# чтобы пакеты config и content импортировались в тестах.


@pytest.fixture(autouse=True)
def media_to_tmp(settings, tmp_path):
    """Тесты с загрузками пишут во временный каталог, а не в рабочий media/."""
    settings.MEDIA_ROOT = tmp_path / "media"
