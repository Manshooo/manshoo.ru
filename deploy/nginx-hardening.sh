#!/usr/bin/env bash
# Донастройка nginx для manshoo.ru (Debian 12, nginx 1.22). Требует root:
#   sudo bash nginx-hardening.sh
#
# Делает три вещи:
#   1. HTTP/2 на обоих сайтах (сейчас HTTP/1.1) — меньше round-trip'ов.
#   2. www.manshoo.ru → 301 на manshoo.ru (сейчас отдаёт копию сайта с кодом 200).
#   3. Basic auth на api.manshoo.ru/django-admin/ — запасная админка Django
#      лежит по общеизвестному пути и не имеет защиты от перебора паролей.
#
# Скрипт идемпотентен. Конфиги azzb.ru не трогает.
# Пароль basic auth: возьмётся из $ADMIN_BASIC_PASS или сгенерируется.
set -euo pipefail

BASIC_USER="${ADMIN_BASIC_USER:-manshoo}"
BASIC_PASS="${ADMIN_BASIC_PASS:-$(openssl rand -base64 15 | tr -d '\n=+/')}"
HTPASSWD=/etc/nginx/.htpasswd-manshoo
STAMP=$(date +%Y%m%d-%H%M%S)

# Пути сертификатов берём из действующих конфигов: certbot мог создать
# каталоги с суффиксом (-0001), угадывать их не надо.
cert_path() { # <config> <directive> <домен по умолчанию>
  local found
  found=$(grep -m1 "^\s*$2" "$1" 2>/dev/null | awk '{print $2}' | tr -d ';' || true)
  if [ -n "$found" ]; then echo "$found"; else echo "/etc/letsencrypt/live/$3/$4"; fi
}

SITE=/etc/nginx/sites-available/manshoo
API=/etc/nginx/sites-available/api.manshoo

SITE_CRT=$(cert_path "$SITE" ssl_certificate manshoo.ru fullchain.pem)
SITE_KEY=$(cert_path "$SITE" ssl_certificate_key manshoo.ru privkey.pem)
API_CRT=$(cert_path "$API" ssl_certificate api.manshoo.ru fullchain.pem)
API_KEY=$(cert_path "$API" ssl_certificate_key api.manshoo.ru privkey.pem)

for f in "$SITE_CRT" "$SITE_KEY" "$API_CRT" "$API_KEY"; do
  [ -f "$f" ] || { echo "!! нет сертификата $f — сначала выпусти его certbot'ом"; exit 1; }
done

echo "== Бэкап текущих конфигов =="
cp -a "$SITE" "$SITE.bak-$STAMP"
cp -a "$API" "$API.bak-$STAMP"

echo "== Пароль для /django-admin =="
if [ -f "$HTPASSWD" ] && [ -z "${ADMIN_BASIC_PASS:-}" ]; then
  echo "   файл $HTPASSWD уже есть — пароль оставляем прежним"
else
  printf '%s:%s\n' "$BASIC_USER" "$(openssl passwd -apr1 "$BASIC_PASS")" >"$HTPASSWD"
  chmod 640 "$HTPASSWD"
  chown root:www-data "$HTPASSWD"
  echo "   логин: $BASIC_USER"
  echo "   пароль: $BASIC_PASS"
  echo "   (это второй пароль — перед формой входа Django; сохрани его)"
fi

echo "== manshoo.ru: HTTP/2 + www → 301 =="
cat >"$SITE" <<NGINX
server {
    listen 443 ssl http2;
    server_name manshoo.ru;

    ssl_certificate $SITE_CRT;
    ssl_certificate_key $SITE_KEY;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

# www — только редирект на основной адрес (иначе сайт доступен по двум адресам)
server {
    listen 443 ssl http2;
    server_name www.manshoo.ru;

    ssl_certificate $SITE_CRT;
    ssl_certificate_key $SITE_KEY;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://manshoo.ru\$request_uri;
}

server {
    listen 80;
    server_name manshoo.ru www.manshoo.ru;

    # чтобы certbot мог продлевать сертификат по HTTP-01
    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }

    location / { return 301 https://manshoo.ru\$request_uri; }
}
NGINX

echo "== api.manshoo.ru: HTTP/2 + basic auth на /django-admin =="
cat >"$API" <<NGINX
server {
    listen 443 ssl http2;
    server_name api.manshoo.ru;

    ssl_certificate $API_CRT;
    ssl_certificate_key $API_KEY;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 10m;

    # Медиа отдаёт nginx напрямую (bind-mount из контейнера api)
    location /media/ {
        alias /var/www/manshoo/media/;
        expires 7d;
    }

    # Запасная админка Django: известный путь, перебором паролей её долбят
    # боты — закрываем вторым паролем ещё до формы входа.
    location /django-admin/ {
        auth_basic "manshoo.ru admin";
        auth_basic_user_file $HTPASSWD;

        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}

server {
    listen 80;
    server_name api.manshoo.ru;

    location ^~ /.well-known/acme-challenge/ { root /var/www/html; }

    location / { return 301 https://api.manshoo.ru\$request_uri; }
}
NGINX

ln -sf "$SITE" /etc/nginx/sites-enabled/manshoo
ln -sf "$API" /etc/nginx/sites-enabled/api.manshoo

echo "== Проверка и перезагрузка =="
if nginx -t; then
  systemctl reload nginx
  echo "   nginx перезагружен"
else
  echo "!! конфиг не прошёл проверку — откатываюсь"
  cp -a "$SITE.bak-$STAMP" "$SITE"
  cp -a "$API.bak-$STAMP" "$API"
  nginx -t && systemctl reload nginx
  exit 1
fi

echo
echo "=== Готово ==="
echo "Проверить снаружи:"
echo "  curl -sI https://www.manshoo.ru/ | head -2        # ждём 301"
echo "  curl -s -o /dev/null -w '%{http_version}\\n' https://manshoo.ru/   # ждём 2"
echo "  curl -s -o /dev/null -w '%{http_code}\\n' https://api.manshoo.ru/django-admin/  # ждём 401"
echo "Бэкапы конфигов: $SITE.bak-$STAMP, $API.bak-$STAMP"
