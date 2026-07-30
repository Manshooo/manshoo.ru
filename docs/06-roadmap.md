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

**Готово, когда:** `docker compose up` поднимает три «hello world»-сервиса ✅ (проверено локально: healthz всех трёх + SSR главной); CI зелёный на PR ⏳ (проверится первым пушем в GitHub).

Заметки по факту: Go в образах — 1.26 (air требует ≥1.26); frontend понадобился `@types/node` для `process.env` в vite-конфиге.

## Phase 1 — Uptime v1 (~3–5 вечеров)

Цель: свой Go-сервис мониторит azzb.ru и шлёт алерты в Telegram. Спека: [05-uptime.md](05-uptime.md).

- [ ] v0-спайк: CLI-проверка azzb.ru по конфигу (1 вечер, цель — пощупать Go).
- [ ] Scheduler + state machine (N неудач → down) + SQLite-хранилище.
- [ ] Telegram-уведомления на переходы up/down.
- [ ] JSON API `/api/status` + `/healthz`; тесты checker'а и state machine.
- [ ] Multi-stage Dockerfile (CGO-free, distroless); CI: build+push в ghcr.
- [ ] Деплой на VPS (`docker-compose.prod.yml`, пока только uptime) — **решается открытый вопрос №1** (что за VPS, есть ли там nginx).

**Готово, когда:** остановка azzb.ru (или тестового монитора) приводит к алерту в Telegram в течение ~3 минут; сервис переживает рестарт без ложных алертов.

## Phase 2 — Сайт MVP (~5–8 вечеров)

Цель: manshoo.ru в проде — главная + портфолио, контент через Django-админку. Спеки: [02-data-model.md](02-data-model.md), [04-seo.md](04-seo.md).

- [ ] api: проект Django + Ninja; модели Profile/Project + миграции; публичные GET-endpoints; Django-админка настроена (list_display, prepopulated slug); healthz.
- [ ] frontend: SvelteKit-скелет; главная (Profile + сетка проектов) и `/projects/[slug]` с SSR-фетчами к api по внутренней сети; Markdown-рендер; минималистичная вёрстка (+ тёмная тема через `prefers-color-scheme` — дёшево сейчас, дорого потом).
- [ ] Типы из OpenAPI-схемы Ninja (`openapi-typescript`) — общий контракт.
- [ ] SEO-база: title/description/canonical, sitemap.xml, robots.txt, OG-теги, 404 (чеклист «База» в [04-seo.md](04-seo.md)).
- [ ] Прод: Caddy (или существующий nginx), TLS, деплой api+frontend+postgres; бэкап-крон pg_dump + media, один раз проверить восстановление.
- [ ] Наполнить: профиль + 2–3 реальных проекта (в т.ч. azzb.ru) через Django-админку.
- [ ] **Добавить манитор manshoo.ru в uptime** (правка config.yaml).
- [ ] Search Console + Яндекс.Вебмастер: подтвердить, отправить sitemap.

**Готово, когда:** manshoo.ru открывается, контент виден с выключенным JS, Lighthouse SEO ≥ 95, uptime следит за обоими доменами.

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
