# manshoo.ru

Личный сайт-портфолио + полигон технологий. Три сервиса в Docker:

| Каталог | Сервис | Стек |
|---|---|---|
| `frontend/` | Публичный сайт (SSR) + админка портфолио | SvelteKit (Svelte 5, TypeScript) |
| `api/` | REST API контента, auth, медиа | Python, Django + Django Ninja, PostgreSQL |
| `uptime/` | Мониторинг личных проектов (azzb.ru, manshoo.ru), алерты в Telegram | Go, SQLite |

## Статус

🚧 Phase 0 (фундамент) готова: dev-окружение, каркасы сервисов, CI. Дальше по плану — uptime-чекер. Вся проектная документация — в [docs/](docs/):

- [docs/README.md](docs/README.md) — карта документации
- [docs/06-roadmap.md](docs/06-roadmap.md) — текущий план работ по фазам
- [docs/decisions/](docs/decisions/) — ADR: почему выбраны именно эти технологии

## Разработка

Нужен Docker (Desktop). Всё остальное живёт в контейнерах:

```
docker compose up --build
```

| Адрес | Что |
|---|---|
| http://localhost:5173 | frontend (vite dev, hot-reload) |
| http://localhost:8000/api/docs | api (Django, OpenAPI-докa Ninja) |
| http://localhost:8080/healthz | uptime |
| localhost:5432 | postgres (manshoo/manshoo, dev-only) |

У всех сервисов hot-reload через volume-mount кода. Проверки — как в CI:

```
docker compose run --rm api sh -c "ruff format --check . && ruff check . && pytest"
```

```
cd frontend && npm run lint && npm run check && npm test
```

```
docker compose run --rm uptime sh -c 'test -z "$(gofmt -l .)" && go vet ./... && go test ./...'
```

Прод: `docker-compose.prod.yml` (заполняется с Phase 1), образы собираются в GitHub Actions → ghcr.io.

## Лицензия

[MIT](LICENSE)
