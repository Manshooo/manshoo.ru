from django.http import HttpRequest
from ninja import NinjaAPI

api = NinjaAPI(title="manshoo.ru API", version="0.1.0")


@api.get("/ping")
def ping(request: HttpRequest) -> dict[str, str]:
    return {"ping": "pong"}
