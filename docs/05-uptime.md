# Uptime-чекер (сервис `uptime/`)

Собственный сервис на Go ([ADR-005](decisions/ADR-005-uptime-go.md)): мониторинг личных проектов + полигон для изучения Go + будущий кейс в портфолио.

**Мониторы на старте:** `azzb.ru` (сразу — сервис приносит пользу ещё до готовности сайта). После деплоя сайта добавляется `manshoo.ru` (правка YAML + redeploy). Поэтому в роадмапе uptime — **Phase 1, раньше сайта**.

## Функциональность v1

- HTTP(S)-проверки по конфигу: интервал, таймаут, ожидаемый статус-код.
- Состояние up/down: `down` после N подряд неудач (default 3) — защита от флапов; повторная проверка при неудаче через короткий ретрай.
- История проверок в SQLite; агрегат «uptime % за 24h/7d/30d» и медианная латентность.
- Telegram-алерты на **переходы** состояния: «🔴 azzb.ru упал (HTTP 502)» / «🟢 azzb.ru поднялся, лежал 12 мин». Не спамить повторами.
- JSON API для сайта (только внутренняя сеть, наружу не публикуется):
  - `GET /api/status` — все мониторы: state, since, uptime_24h/7d/30d, latency_ms
  - `GET /api/monitors/{slug}` — история/агрегаты для графика
  - `GET /healthz` — liveness для docker healthcheck
- Бонус v1.1: проверка срока TLS-сертификата, предупреждение в Telegram за 14 дней.

## Конфиг (`uptime/config.yaml`)

```yaml
telegram:            # token и chat_id — из env, не из файла
  enabled: true
defaults:
  interval: 60s
  timeout: 10s
  failures_to_down: 3
monitors:
  - slug: azzb
    name: azzb.ru
    url: https://azzb.ru
    expect_status: 200
  # - slug: manshoo        # добавить после деплоя сайта (Phase 2)
  #   name: manshoo.ru
  #   url: https://manshoo.ru
```

## Структура Go-проекта

```
uptime/
  cmd/uptime/main.go        # wiring: конфиг, store, scheduler, http
  internal/config/          # парсинг YAML + env
  internal/checker/         # HTTP-проверка одной цели (чистая функция — легко тестировать)
  internal/scheduler/       # тикеры per-monitor, джиттер, ретраи
  internal/store/           # SQLite: запись проверок, агрегаты, retention
  internal/notify/          # Telegram (интерфейс Notifier — для тестов и будущих каналов)
  internal/api/             # chi-роутер: /api/status, /healthz
```

Зависимости — минимум, идиоматичный стиль: stdlib `net/http` + `chi` (роутер), `modernc.org/sqlite` (без CGO → простой multi-stage build в scratch/distroless), YAML-парсер. Никаких ORM и фреймворков — цель в том числе учебная.

Хранение: ретенция сырых проверок 90 дней (фоновая чистка), state переживает рестарт (читается из SQLite при старте — рестарт не порождает ложных алертов).

## Интеграция с портфолио (Phase 4)

- `Project.uptime_monitor_slug` связывает проект с монитором.
- Карточка проекта: бейдж «🟢 online · 99.9% за 30 дней» — frontend при SSR ходит в `http://uptime:8080/api/status` (кэш в памяти 30–60 сек, при недоступности чекера бейдж просто не показывается — graceful degradation).
- Страница `/status`: публичная сводка всех мониторов с графиком латентности (данные проксируются через frontend server route — чекер остаётся не опубликованным наружу).

## Ограничение и его компенсация

Чекер на том же VPS, что и manshoo.ru, не увидит падение самого VPS. Компенсация в v1.1: чекер каждые N минут пингует внешний dead-man's-switch (healthchecks.io, бесплатный) — если пинги пропали, healthchecks сам шлёт алерт «чекер молчит». Стратегически (бэклог): вынести чекер на отдельный бесплатный хост — тогда он «смотрит снаружи», как и положено.

## Роадмап сервиса

1. **v0 (спайк, 1 вечер):** CLI: прочитать конфиг, проверить azzb.ru, вывести результат. Цель — пощупать Go-структуру.
2. **v1:** демон: scheduler + SQLite + Telegram + JSON API + Docker + деплой. Мониторим azzb.ru. ← конец Phase 1
3. **v1.1:** TLS-expiry, heartbeat на healthchecks.io, retention.
4. **v2:** интеграция с портфолио: бейджи, `/status` (Phase 4).
5. **бэклог:** история инцидентов, графики латентности, вынос на отдельный хост, ICMP/TCP-проверки.
