#!/usr/bin/env bash
# Ночной бэкап manshoo.ru: postgres (pg_dump), media, SQLite uptime-чекера.
# Живёт в /var/www/manshoo/backup.sh, запускается из crontab manshoo_user:
#   10 4 * * * /var/www/manshoo/backup.sh >> /var/www/manshoo/backups/backup.log 2>&1
set -euo pipefail
cd /var/www/manshoo
mkdir -p backups
STAMP=$(date +%F)

docker compose -f docker-compose.prod.yml exec -T postgres pg_dump -U manshoo manshoo |
  gzip >"backups/db-$STAMP.sql.gz"
docker compose -f docker-compose.prod.yml cp uptime:/data/uptime.db "backups/uptime-$STAMP.db" >/dev/null
tar czf "backups/media-$STAMP.tar.gz" media

# Ретенция: 14 дампов БД и uptime, 7 архивов media
ls -1t backups/db-*.sql.gz 2>/dev/null | tail -n +15 | xargs -r rm --
ls -1t backups/uptime-*.db 2>/dev/null | tail -n +15 | xargs -r rm --
ls -1t backups/media-*.tar.gz 2>/dev/null | tail -n +8 | xargs -r rm --

echo "$(date -Is) backup ok: db-$STAMP.sql.gz, uptime-$STAMP.db, media-$STAMP.tar.gz"
