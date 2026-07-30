#!/usr/bin/env bash
# Одноразовая настройка VPS для manshoo.ru (Debian 12, 1 ГБ RAM).
# Запуск под root:  sudo bash bootstrap-vps.sh
# Скрипт идемпотентен — повторный запуск безопасен.
set -euo pipefail

DEPLOY_DIR=/var/www/manshoo
RUNNER_HOME=/home/manshoo_user/actions-runner

echo "== 1/7 Swap 2G (RAM всего 1 ГБ) =="
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 2G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
fi

echo "== 2/7 Базовые пакеты =="
apt-get update -qq
apt-get install -y -qq git ca-certificates curl

echo "== 3/7 Docker (официальный репозиторий) =="
if ! command -v docker >/dev/null; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    >/etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
usermod -aG docker manshoo_user
# Раскомментируй, если docker нужен и проекту azzb:
# usermod -aG docker azzb_user

echo "== 4/7 Каталог деплоя и секреты =="
mkdir -p "$DEPLOY_DIR"/api "$DEPLOY_DIR"/uptime "$DEPLOY_DIR"/media
if [ ! -f "$DEPLOY_DIR/api/.env" ]; then
  cat >"$DEPLOY_DIR/api/.env" <<EOF
SECRET_KEY=$(openssl rand -base64 48 | tr -d '\n=+/')
DEBUG=0
# «api» — имя сервиса в docker-сети: так к Django ходит SSR-фронтенда
ALLOWED_HOSTS=api.manshoo.ru,127.0.0.1,localhost,api
CSRF_TRUSTED_ORIGINS=https://api.manshoo.ru,https://manshoo.ru
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=manshoo
POSTGRES_USER=manshoo
POSTGRES_PASSWORD=$(openssl rand -hex 24)
DJANGO_SUPERUSER_USERNAME=manshoo
DJANGO_SUPERUSER_EMAIL=yanislavpic@gmail.com
DJANGO_SUPERUSER_PASSWORD=$(openssl rand -base64 15 | tr -d '\n=+/')
EOF
fi
touch "$DEPLOY_DIR/uptime/.env" # сюда TELEGRAM_BOT_TOKEN=... и TELEGRAM_CHAT_ID=...
chown -R manshoo_user:www-data "$DEPLOY_DIR"
chmod 600 "$DEPLOY_DIR/api/.env" "$DEPLOY_DIR/uptime/.env"
# uid 1000 — пользователь appuser внутри контейнера api (пишет загрузки), gid 33 — www-data (nginx читает)
chown 1000:33 "$DEPLOY_DIR/media"

echo "== 5/7 GitHub Actions runner как systemd-сервис =="
if [ -d "$RUNNER_HOME" ] && [ ! -f "$RUNNER_HOME/.service" ]; then
  (cd "$RUNNER_HOME" && ./svc.sh install manshoo_user && ./svc.sh start)
fi

echo "== 6/7 nginx: manshoo.ru → :3000 (frontend), api.manshoo.ru → :8000 (api) =="
cat >/etc/nginx/sites-available/manshoo <<'NGINX'
server {
    server_name manshoo.ru www.manshoo.ru;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/manshoo.ru/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/manshoo.ru/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}
server {
    if ($host = www.manshoo.ru) {
        return 301 https://$host$request_uri;
    } # managed by Certbot
    if ($host = manshoo.ru) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name manshoo.ru www.manshoo.ru;
    return 404; # managed by Certbot
}
NGINX

cat >/etc/nginx/sites-available/api.manshoo <<'NGINX'
server {
    listen 80;
    server_name api.manshoo.ru;

    client_max_body_size 10m;

    # Медиа отдаёт nginx напрямую (bind-mount из контейнера api)
    location /media/ {
        alias /var/www/manshoo/media/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/manshoo /etc/nginx/sites-enabled/manshoo
ln -sf /etc/nginx/sites-available/api.manshoo /etc/nginx/sites-enabled/api.manshoo
nginx -t && systemctl reload nginx

echo "== 7/7 TLS для api.manshoo.ru =="
if [ ! -d /etc/letsencrypt/live/api.manshoo.ru ]; then
  certbot --nginx -d api.manshoo.ru --non-interactive --agree-tos --no-eff-email ||
    echo "!! certbot не справился — проверь DNS api.manshoo.ru и повтори вручную: certbot --nginx -d api.manshoo.ru"
fi

echo
echo "=== Готово ==="
echo "1. Runner запущен — очередь деплоев в GitHub Actions поедет сама."
echo "2. Пароль Django-админки: DJANGO_SUPERUSER_PASSWORD в $DEPLOY_DIR/api/.env"
echo "3. Telegram-алерты: заполни $DEPLOY_DIR/uptime/.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID),"
echo "   затем: cd $DEPLOY_DIR && docker compose -f docker-compose.prod.yml up -d uptime"
