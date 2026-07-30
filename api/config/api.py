from django.http import HttpRequest
from ninja import NinjaAPI

from content.api import router as content_router

api = NinjaAPI(title="manshoo.ru API", version="0.1.0")

api.add_router("", content_router)


@api.get("/ping")
def ping(request: HttpRequest) -> dict[str, str]:
    return {"ping": "pong"}
