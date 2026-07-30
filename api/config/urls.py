from django.contrib import admin
from django.http import HttpRequest, JsonResponse
from django.urls import path

from .api import api


def healthz(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("healthz", healthz),
    path("api/", api.urls),
]
