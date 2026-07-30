from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.urls import path

from .api import api


def healthz(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def robots(request: HttpRequest) -> HttpResponse:
    # api.manshoo.ru индексировать нечего
    return HttpResponse("User-agent: *\nDisallow: /\n", content_type="text/plain")


urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("healthz", healthz),
    path("robots.txt", robots),
    path("api/", api.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
