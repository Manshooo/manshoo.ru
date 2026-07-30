# Роадмап

Фазы маленькие, каждая заканчивается **работающим и задеплоенным** результатом. Ориентир длительности — в «вечерах» (~2–3 часа), оценка грубая. Внутри фазы порядок задач сверху вниз.

Uptime идёт раньше сайта осознанно: он полезен уже сейчас (мониторинг azzb.ru), маленький по объёму и даёт быстрый цикл «выучил Go-кусочек → задеплоил». Если захочется скорее увидеть сайт — фазы 1 и 2 можно поменять местами без последствий.

## Phase 0 — Фундамент (~1–2 вечера) — ✅ выполнена 2026-07-30

Цель: репозиторий из каркаса становится рабочей средой.

- [x] Заполнить `.gitignore` (python, node, go, .env, media, sqlite, IDE).
- [x] `docker-compose.yml` (dev) со всеми сервисами и hot-reload; `.env.example` для каждого сервиса.
- [x] Заготовки CI в трёх workflow: lint+test с `paths:`-фильтрами (пока проверяют «hello world»).
- [x] Линтеры/форматтеры: ruff (api), eslint+prettier (frontend), golangci-lint (uptime); Dependabot.
- [x] Корневой README: что это, как поднять dev-окружение, ссылка на docs/.

**Готово, когда:** `docker compose up` поднимает три «hello world»-сервиса ✅ (проверено локально: healthz всех трёх + SSR главной); CI зелёный ✅ (api/frontend/uptime на main).

Заметки по факту: Go в образах — 1.26 (air требует ≥1.26); frontend понадобился `@types/node` для `process.env` в vite-конфиге; тестам api в CI нужен `SECRET_KEY` через env workflow. Dependabot при первом же скане открыл PR-ы, часть с красными мажорами (typescript 7, vite-plugin-svelte 7 → требует vite 7) — разобрать при случае.

## Phase 1 — Uptime v1 (~3–5 вечеров) — ✅ завершена 2026-07-30 (в проде)

Цель: свой Go-сервис мониторит azzb.ru и шлёт алерты в Telegram. Спека: [05-uptime.md](05-uptime.md).

- [x] ~~v0-спайк~~ — объединён с v1, сервис написан целиком.
- [x] Scheduler + state machine (N неудач → down, ускоренные перепроверки) + SQLite-хранилище.
- [x] Telegram-уведомления на переходы up/down (без токена — фолбэк в лог).
- [x] JSON API `/api/status`, `/api/monitors/{slug}` + `/healthz`; тесты всех пакетов.
- [x] Multi-stage Dockerfile (CGO-free, distroless, 22 МБ, флаг `-healthcheck`); CI пушит образ: `ghcr.io/manshooo/manshoo.ru-uptime`.
- [x] Деплой на VPS: bootstrap выполнен владельцем 2026-07-30, uptime в проде мониторит azzb.ru и manshoo.ru.
- [ ] Telegram-алерты: env заполнен, но `api.telegram.org` заблокирован с хостинга → нужен прокси (`TELEGRAM_API_BASE`, воркер в [deploy/telegram-proxy-worker.js](../deploy/telegram-proxy-worker.js)) и **перевыпуск токена** (старый утёк в логи из-за бага логирования — исправлен, см. [05-uptime.md](05-uptime.md)).

**Готово, когда:** остановка azzb.ru (или тестового монитора) приводит к алерту в Telegram в течение ~3 минут (переходы проверены тестами и живым контейнером; реальный Telegram — на деплое); сервис переживает рестарт без ложных алертов ✅ (состояние читается из SQLite — проверено рестартом контейнера).

Заметки по факту: роутер — stdlib вместо chi (Go 1.22+ умеет методы и `{slug}`, см. [05-uptime.md](05-uptime.md)); golangci-lint строже `go vet` — errcheck требует явного `_ =` даже на отложенных Close.

## Phase 2 — Сайт MVP (~5–8 вечеров) — ✅ в проде 2026-07-30; хвосты — за владельцем

Цель: manshoo.ru в проде — главная + портфолио, контент через Django-админку. Спеки: [02-data-model.md](02-data-model.md), [04-seo.md](04-seo.md).

- [x] api: приложение `content` — модели Profile/Project + миграции + сид (профиль, кейс manshoo-ru, azzb-ru черновиком); публичные GET-endpoints (Ninja); Django-админка настроена (fieldsets, list_editable, prepopulated slug); whitenoise для статики.
- [x] frontend: главная (Profile + сетка проектов) и `/projects/[slug]` с SSR-фетчами к api по внутренней сети; Markdown (marked); минимализм + тёмная тема (`prefers-color-scheme`); тесты markdown/format.
- [x] Типы контракта: вручную в `src/lib/types.ts` (осознанное упрощение — генерация из OpenAPI в Phase 3, см. [02-data-model.md](02-data-model.md)).
- [x] SEO-база: title/description/canonical, OG-теги (og:image — в Phase 4 с генератором), sitemap.xml с lastmod, robots.txt, честные 404, favicon.
- [x] Прод-обвязка: системный nginx (конфиги в bootstrap), TLS certbot, compose api+frontend+postgres, deploy-джобы.
- [x] **Деплой**: manshoo.ru и api.manshoo.ru живы (nginx → контейнеры, TLS ок, редиректы ок, честные 404).
- [x] Бэкап-крон (04:10): pg_dump + media + sqlite uptime, ретенция 14/7; восстановление проверено в restore_test (2 проекта, профиль).
- [ ] Наполнить контент: отредактировать профиль, дописать и опубликовать azzb.ru через `api.manshoo.ru/django-admin/` (логин `manshoo`, пароль — в `/var/www/manshoo/api/.env`).
- [x] Монитор manshoo.ru в uptime — оба монитора `up`.
- [ ] Search Console + Яндекс.Вебмастер: подтвердить домен, отправить sitemap (действие владельца — нужны его аккаунты).
- [ ] Замерить Lighthouse (критерий SEO ≥ 95) — не гонялся.

**Готово, когда:** manshoo.ru открывается ✅, контент виден с выключенным JS ✅, Lighthouse SEO ≥ 95 ⏳, uptime следит за обоими доменами ✅.

Заметки по факту: `ALLOWED_HOSTS` обязан включать docker-имя сервиса `api` — SSR ходит по внутренней сети с `Host: api:8000`, иначе 400 → SvelteKit отдаёт 502 (наступили при первом деплое, чинится в bootstrap); www.manshoo.ru пока отдаёт 200 вместо 301 на apex — canonical прикрывает, поправить nginx при следующем sudo-заходе.

## Phase 3 — Своя админка (~4–6 вечеров)

Цель: полный цикл управления контентом без Django-админки. Спека: [03-admin-editor.md](03-admin-editor.md).

- [ ] api: session-auth endpoints, CSRF, rate limit, admin CRUD + upload обложки (Pillow-пересохранение).
- [ ] frontend: `/admin`-группа (CSR, noindex), login, список проектов, форма проекта (markdown-превью, tag-input, highlights-список, drag&drop обложки), форма профиля.
- [ ] Предпросмотр черновика `?preview=1`.
- [ ] `/django-admin` закрыть basic auth на прокси (остаётся страховкой).

**Готово, когда:** критерий из [03-admin-editor.md](03-admin-editor.md) — весь цикл от логина до публикации в своём UI.

## Phase 4 — Интеграции и полировка (~3–5 вечеров)

- [ ] Живые статус-бейджи проектов из uptime API (graceful degradation).
- [ ] Публичная страница `/status` со сводкой мониторов.
- [ ] JSON-LD (Person, WebSite, CreativeWork/SoftwareSourceCode, BreadcrumbList).
- [ ] OG-картинки per-project (генерация).
- [ ] Lighthouse CI в workflow frontend; добить Performance ≥ 95.
- [ ] uptime v1.1: TLS-expiry алерты, heartbeat на healthchecks.io, retention.

**Готово, когда:** карточки показывают живой статус; rich-превью ссылок в Telegram/соцсетях красивое; оба валидатора разметки без ошибок.

## Phase 5 — Развитие

Пул: [07-ideas.md](07-ideas.md). Первые кандидаты — блог (SEO-трафик) и PDF-резюме из данных портфолио. Решать по настроению после Phase 4.

## Правила движения

- Одна фаза = одна ветка/серия PR; после фазы — git-тег `phase-N` и правка чекбоксов здесь.
- Разошлись с планом → сначала правим docs/ADR, потом код.
- Не начинать следующую фазу, пока у текущей не выполнены «Готово, когда».
