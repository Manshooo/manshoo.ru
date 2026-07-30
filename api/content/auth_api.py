from django.contrib.auth import authenticate, login, logout
from django.core.cache import cache
from django.http import HttpRequest
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja.utils import check_csrf

router = Router(tags=["auth"])

LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 60


class LoginIn(Schema):
    username: str
    password: str


class MeOut(Schema):
    username: str


class CsrfOut(Schema):
    csrf_token: str


def client_ip(request: HttpRequest) -> str:
    # За nginx реальный адрес приходит в X-Forwarded-For
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


@router.get("/csrf", response=CsrfOut, auth=None)
def csrf(request: HttpRequest):
    """Отдаёт csrf-токен: админка шлёт его заголовком X-CSRFToken.

    Куку ставит CsrfViewMiddleware — get_token() помечает запрос как
    нуждающийся в ней (декоратор ensure_csrf_cookie здесь не подходит:
    операции ninja возвращают dict, а не HttpResponse).
    """
    return {"csrf_token": get_token(request)}


@router.post("/login", response=MeOut, auth=None)
def login_view(request: HttpRequest, data: LoginIn):
    # Операции ninja csrf-exempt, а логин защищать надо (login-CSRF).
    # Django-декораторы поверх операций не работают — они ждут HttpResponse,
    # а операция возвращает dict; поэтому проверяем тем же helper'ом,
    # которым пользуется cookie-аутентификация ninja.
    if check_csrf(request, login_view) is not None:
        raise HttpError(403, "CSRF-токен не прошёл проверку")

    key = f"login-attempts:{client_ip(request)}"
    if cache.get(key, 0) >= LOGIN_ATTEMPTS:
        raise HttpError(429, "Слишком много попыток входа, подождите минуту")

    user = authenticate(request, username=data.username, password=data.password)
    if user is None or not user.is_staff:
        # Счётчик заводим только при неудаче: успешные входы лимит не тратят
        cache.set(key, cache.get(key, 0) + 1, LOGIN_WINDOW_SECONDS)
        raise HttpError(401, "Неверный логин или пароль")

    login(request, user)
    cache.delete(key)
    return {"username": user.get_username()}


@router.post("/logout", auth=django_auth)
def logout_view(request: HttpRequest):
    logout(request)
    return {"ok": True}


@router.get("/me", response=MeOut, auth=django_auth)
def me(request: HttpRequest):
    return {"username": request.user.get_username()}
