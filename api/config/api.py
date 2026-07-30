from django.http import HttpRequest
from ninja import NinjaAPI

from content.admin_api import router as admin_router
from content.api import router as content_router
from content.auth_api import router as auth_router

# CSRF: django_auth (cookie-аутентификация ninja) сам проверяет X-CSRFToken
# на небезопасных методах — отдельный флаг у NinjaAPI для этого не нужен.
# Логин защищён @csrf_protect вручную (см. content/auth_api.py).
api = NinjaAPI(title="manshoo.ru API", version="0.2.0")

api.add_router("", content_router)
api.add_router("/auth", auth_router)
api.add_router("/admin", admin_router)


@api.get("/ping")
def ping(request: HttpRequest) -> dict[str, str]:
    return {"ping": "pong"}
