# Модель данных и API

Живёт в сервисе `api` (Django). Принцип: минимум таблиц, JSONB для списков, которые не требуют реляционных запросов.

## Project — проект портфолио

Портфолио заменяет «Опыт работы» в резюме, поэтому у проекта есть и «резюмные» поля (роль, организация, период, достижения), и «витринные» (обложка, фишки, ссылки).

| Поле | Тип | Назначение |
|---|---|---|
| `slug` | slug, unique | URL: `/projects/<slug>` |
| `title` | char(120) | Название |
| `tagline` | char(200) | Одна строка «что это» — для карточки в списке |
| `description_md` | text | Полное описание, Markdown |
| `role` | char(120) | Роль: «Backend-разработчик», «Автор и единственный разработчик» |
| `org` | char(120), blank | Компания/контекст («пет-проект», «Компания X») — для резюме-вью |
| `project_type` | choice | `work` / `pet` / `oss` / `freelance` |
| `period_start` | date | Начало (для резюме важен порядок) |
| `period_end` | date, null | `null` = «по настоящее время» |
| `stack` | JSONB: `["Go", "PostgreSQL"]` | Теги стека; фильтрация через `__contains` |
| `highlights` | JSONB: `[str]` | «Ключевые фишки» — 3–7 буллетов: чем горжусь, цифры, сложности |
| `links` | JSONB: `{live, repo, case}` | Ссылки: продакшен, репозиторий, статья/кейс |
| `cover` | image, null | Обложка карточки |
| `status` | choice | `active` / `wip` / `archived` — бейдж на карточке |
| `is_published` | bool, default False | Черновики не видны публично |
| `is_featured` | bool | Закреплён вверху главной |
| `sort_order` | int | Ручной порядок внутри групп |
| `uptime_monitor_slug` | char, blank | Связь с монитором uptime-чекера → живой статус-бейдж на карточке (Phase 4) |
| `created_at` / `updated_at` | auto | Служебные; `updated_at` идёт в sitemap `lastmod` |

Индексы: `slug` (unique), `(is_published, sort_order)`. Отдельная таблица тегов не нужна на этом масштабе — если понадобится страница «все проекты на Go», JSONB-фильтра достаточно ([ADR-004](decisions/ADR-004-database-postgres.md)).

## Profile — singleton «обо мне»

Редактируемая через админку альтернатива хардкоду текстов на главной.

| Поле | Тип | Назначение |
|---|---|---|
| `name` | char | Имя |
| `headline` | char(200) | «Кто я» одной строкой — заголовок главной |
| `bio_md` | text | Абзац-два о себе, Markdown |
| `photo` | image, null | Фото/аватар |
| `location` | char, blank | Город/часовой пояс |
| `skills` | JSONB: `[str]` | Ключевые навыки — строка тегов на главной |
| `socials` | JSONB: `{github, telegram, email, ...}` | Контакты |
| `meta_description` | char(160) | SEO-описание главной |

Реализация singleton: `pk=1`, `load()`-classmethod. Django-админка редактирует его с первого дня.

## API (Django Ninja)

Ninja даёт OpenAPI-схему из коробки (`/api/docs`). В Phase 2 TS-типы написаны вручную (`frontend/src/lib/types.ts` — контракт из трёх интерфейсов, зеркалит `content/schemas.py`); генерацию через `openapi-typescript` включим в Phase 3, когда контракт вырастет админскими эндпоинтами.

### Публичное (без auth)

```
GET /api/profile                     → Profile
GET /api/projects                    → [ProjectCard]  (published, сортировка: featured, sort_order, -period_start)
GET /api/projects/{slug}             → ProjectDetail  (404 для неопубликованных без сессии)
```

### Админское (сессия Django + CSRF)

```
POST   /api/auth/login | POST /api/auth/logout | GET /api/auth/me
GET    /api/admin/projects           → все, включая черновики
POST   /api/admin/projects
PUT    /api/admin/projects/{id}
DELETE /api/admin/projects/{id}
POST   /api/admin/projects/{id}/cover   (multipart upload)
PUT    /api/admin/profile
```

### Внутреннее (для SSR)

`GET /api/projects/{slug}?preview=1` — с валидной сессией отдаёт и черновик (предпросмотр из админки).

## Данные uptime-сервиса

У `uptime` своя SQLite (сервисы не делят БД):

```
monitors: из YAML-конфига (slug, name, url, interval_s, timeout_s, expect_status)
checks:   (monitor_slug, ts, ok, http_status, latency_ms, error)
state:    текущее состояние монитора (up/down, since, last_alert_ts)
```

Контракт связи с сайтом — только `Project.uptime_monitor_slug` ↔ `monitors.slug` и JSON API чекера ([05-uptime.md](05-uptime.md)).
