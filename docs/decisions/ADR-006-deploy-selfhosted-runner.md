# ADR-006: Деплой через self-hosted runner; маршрутизация через системный nginx

**Status:** Accepted
**Date:** 2026-07-30
**Deciders:** Yanislav Pichugin

## Context

Прод — один VPS (Debian 12, 1 ГБ RAM) на два проекта: azzb.ru (уже живёт за системным nginx + uWSGI) и manshoo.ru (пользователь `manshoo_user`, каталог `/var/www/manshoo`). Владелец явно попросил деплой через GitHub Actions runner'ы на самом сервере. Docker на VPS изначально отсутствовал; root-доступа у автоматизации нет — только одноразовый bootstrap, который владелец запускает сам под sudo.

## Decision

1. **Self-hosted runner** в репозитории (label `manshoo`), работает как systemd-сервис под `manshoo_user`. Деплой-джобы (`runs-on: [self-hosted, manshoo]`) выполняются прямо на VPS: checkout → sync файлов в `/var/www/manshoo` → `docker compose pull/up` → health-проверка.
2. **Reverse-proxy — существующий системный nginx** (не Caddy): manshoo.ru → 127.0.0.1:3000 (frontend SSR), api.manshoo.ru → 127.0.0.1:8000 (api), `/media/` отдаёт nginx из bind-mount. Контейнеры публикуют порты только на 127.0.0.1.
3. **Одноразовый bootstrap** (`deploy/bootstrap-vps.sh`, запускает владелец под sudo): swap 2G, docker, каталог деплоя, генерация секретов в `/var/www/manshoo/api/.env`, установка runner-сервиса, nginx-конфиги, certbot для api.manshoo.ru. Идемпотентен.

## Options Considered

### Option A: Деплой по ssh из облачного раннера

| Dimension | Assessment |
|-----------|------------|
| Простота | Med — нужен деплой-ключ в GitHub Secrets, ssh-обвязка в jobs |
| Безопасность | Med — приватный ключ от сервера лежит в GitHub |
| Соответствие желанию владельца | Low — просили именно runner'ы на сервере |

### Option B: Self-hosted runner на VPS (выбран)

| Dimension | Assessment |
|-----------|------------|
| Простота jobs | High — деплой-шаги это просто shell на целевой машине |
| Безопасность | Med/High — секреты сервера не покидают сервер; runner имеет доступ к docker (эквивалент root — принято: репозиторий свой, PR чужих не выполняются на self-hosted без апрува) |
| Ресурсы | Cost: ~150 МБ RAM под idle-listener на 1-гиговой машине — принято, добавлен swap |

### Option C: Caddy в docker вместо системного nginx

Отклонён: 80/443 уже заняты системным nginx, который обслуживает azzb.ru; второй edge-прокси на той же машине — конфликт портов и лишняя сущность.

## Trade-off Analysis

Вариант B меняет «секреты сервера в GitHub» на «агент GitHub на сервере» — для личного репозитория это лучший баланс: джобы тривиальны, а bootstrap с sudo выполняется владельцем один раз. Плата — RAM под runner и дисциплина «на self-hosted не выполняются чужие PR» (дефолтные настройки GitHub для форков этого и не делают без апрува).

## Consequences

- Деплой любого сервиса = push в main (paths-фильтры выбирают, что деплоить); джобы ждут в очереди, если runner офлайн.
- nginx-конфиги меняются только через bootstrap/root — правки редки; референс-копии лежат в `deploy/nginx/`… (встроены в bootstrap heredoc'ами, чтобы скрипт был самодостаточным).
- Пока runner не запущен (до bootstrap) деплой-джобы висят в очереди — это ожидаемое состояние, не ошибка.
- Ревизит: если появится второй сервер или нагрузка — вернуться к варианту A/контейнерному runner'у.

## Action Items

1. [x] Runner зарегистрирован (`manshoo-vps`, label `manshoo`).
2. [ ] Владелец: `scp` bootstrap → `sudo bash bootstrap-vps.sh` (запускает всё: docker, runner-сервис, nginx, TLS).
3. [x] Deploy-джобы во всех трёх workflow.
