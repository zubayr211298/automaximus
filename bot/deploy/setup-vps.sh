#!/usr/bin/env bash
# Automaximus bot uchun toza Ubuntu VPS'ni bir martalik sozlash skripti.
#
# Foydalanish (server ustida, root sifatida):
#   1) Shu papkani (bot/) serverga nusxalang, masalan:
#        scp -r bot/ root@SERVER_IP:/opt/avtomaximus-bot
#   2) Serverga ulaning: ssh root@SERVER_IP
#   3) cd /opt/avtomaximus-bot/deploy && DOMAIN=bot.sizningdomeningiz.uz bash setup-vps.sh
#
# DOMAIN berilmasa, server shu zahoti https://bot.SERVER_IP.sslip.io orqali ham ishlaydi
# (domen hali sotib olinmagan bo'lsa ham test qilish uchun).
set -euo pipefail

APP_DIR="/opt/avtomaximus-bot"
SERVICE_NAME="avtomaximus-bot"
DOMAIN="${DOMAIN:-}"

if [[ -z "$DOMAIN" ]]; then
  SERVER_IP="$(curl -fsSL https://api.ipify.org || echo "")"
  if [[ -z "$SERVER_IP" ]]; then
    echo "DOMAIN berilmadi va server IP'sini aniqlab bo'lmadi. DOMAIN=... bilan qayta ishga tushiring." >&2
    exit 1
  fi
  DOMAIN="bot.${SERVER_IP}.sslip.io"
  echo "DOMAIN berilmagani uchun vaqtinchalik manzil ishlatiladi: https://${DOMAIN}"
fi

echo "==> Python3 va Caddy o'rnatilmoqda..."
apt-get update -qq
apt-get install -y -qq python3 python3-venv curl debian-keyring debian-archive-keyring apt-transport-https >/dev/null

if ! command -v caddy >/dev/null; then
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list >/dev/null
  apt-get update -qq
  apt-get install -y -qq caddy >/dev/null
fi

if [[ ! -f "${APP_DIR}/bot.py" ]]; then
  echo "${APP_DIR}/bot.py topilmadi. Avval bot/ papkasini serverga ko'chiring:" >&2
  echo "    scp -r bot/ root@SERVER_IP:${APP_DIR}" >&2
  exit 1
fi

if [[ ! -f "${APP_DIR}/.env" ]]; then
  cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
  echo "!!! ${APP_DIR}/.env yaratildi — BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_IDS ni to'ldiring, so'ng:"
  echo "    nano ${APP_DIR}/.env"
fi

echo "ALLOWED_ORIGIN avtomatik sozlanmaydi — sayt domeningizni .env ichida qo'lda yozing."

id -u www-data >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin www-data
chown -R www-data:www-data "$APP_DIR"

echo "==> systemd xizmati sozlanmoqda..."
cp "${APP_DIR}/avtomaximus-bot.service" "/etc/systemd/system/${SERVICE_NAME}.service"
systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"

echo "==> Caddy (avtomatik HTTPS) sozlanmoqda, domen: ${DOMAIN}..."
cat > /etc/caddy/Caddyfile <<EOF
${DOMAIN} {
    reverse_proxy localhost:8080
}
EOF
systemctl reload caddy || systemctl restart caddy

echo ""
echo "==> Tayyor."
echo "    Bot holati: systemctl status ${SERVICE_NAME}"
echo "    Jurnal:     journalctl -u ${SERVICE_NAME} -f"
echo "    Tekshirish: curl https://${DOMAIN}/health   (BOT_TOKEN to'ldirilmaguncha bot o'chiq bo'ladi)"
echo ""
echo "Keyingi qadam: ${APP_DIR}/.env ni to'ldirib, qayta ishga tushiring:"
echo "    systemctl restart ${SERVICE_NAME}"
