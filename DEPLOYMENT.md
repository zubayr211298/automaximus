# Automaximus — joylashtirish (deployment)

Hammasi **Dokploy**'da (Hostinger VPS) ishlaydi. Vercel ishlatilmaydi (loyihalar 2026-11-12 da o'chirilgan).

Dokploy paneli: `http://179.67.192.130:3000` — loyiha `automaximus`, muhit `production`.

| Ilova | Papka | Manzil | Port |
|---|---|---|---|
| `api` (bot) | `bot/` | https://bot.179.67.192.130.sslip.io | 8080 |
| `client` (Mini App) | `mini-app/` | https://app.179.67.192.130.sslip.io | 3000 |
| `sayt` | `sayt/` | https://sayt.179.67.192.130.sslip.io | 80 |

`sslip.io` — vaqtinchalik manzil (domensiz HTTPS). Haqiqiy domen olinsa, "Domenga o'tish" bo'limiga qarang.

## Avtomatik deploy

GitHub repo → Settings → Webhooks da uchta `push` webhook bor (har ilova uchun bittadan). Manzillari Dokploy'dagi
ilovaning **Deployments** tabidagi *Webhook URL*. `main` ga push qilinsa, uchala ilova qayta build bo'ladi
(navbat bilan, bir necha daqiqa ichida).

Muhit o'zgaruvchisi (Environment) o'zgarganda webhook qayta ishga tushirmaydi — Dokploy'da ilova → **General → Deploy** bosing.

## Qanday sozlangan (qayta yaratish kerak bo'lsa)

Har bir ilova: **Provider = Git**, repo `https://github.com/zubayr211298/automaximus.git`, branch `main`,
**Build Path `/`**, **Build Type = Dockerfile**:

| Ilova | Docker File | Docker Context Path |
|---|---|---|
| `api` | `bot/Dockerfile` | `bot` |
| `client` | `mini-app/Dockerfile` | `mini-app` |
| `sayt` | `sayt/Dockerfile` | `sayt` |

(Build Path'ga `/bot` yozish bo'sh context beradi — shuning uchun `/` va to'liq yo'llar.)

**`api` (bot):**
- Environment: `BOT_TOKEN` (faqat Dokploy'da, repoga yozilmaydi), `ADMIN_CHAT_ID`, `ADMIN_IDS`, `ALLOWED_ORIGIN=*`, `LEAD_PORT=8080`.
- Advanced → Volumes: Volume Mount `bot-data` → `/data` (baza shu yerda; deploydan o'chib ketmaydi).
- Domains: bot manzili, Container Port `8080`, HTTPS + Let's Encrypt.
- Bot har 24 soatda baza nusxasini admin chatga yuboradi (`bot/README.md` da tiklash yo'riqnomasi).

**`client` (Mini App):**
- Environment → *Build-time Arguments*: `NEXT_PUBLIC_BOT_API_URL=https://bot.179.67.192.130.sslip.io`
  (build vaqtida kodga yoziladi, o'zgarsa qayta build kerak).
- Domains: Container Port `3000`, HTTPS + Let's Encrypt.
- BotFather → botni tanlang → **Bot Settings → Menu Button** → URL = Mini App manzili, nomi `Yozilish`.

**`sayt`:**
- Domains: Container Port `80`, HTTPS + Let's Encrypt.
- Formaning manzili `sayt/index.html` ichida (`leadUrl`) — bot manzili + `/lead`.
- `sayt/nginx.conf` HTML/JS ni `no-cache` bilan beradi (telefonda eski nusxa qolmasligi uchun).

## Domenga o'tish (haqiqiy domen olinganda)

1. Domen DNS'ida `A` yozuvlar: `bot`, `app`, `sayt` (yoki asosiy domen) → `179.67.192.130`.
2. Dokploy'da har ilovaning **Domains** bo'limida yangi domen qo'shing (HTTPS + Let's Encrypt), eskisini o'chiring.
3. `client` → Environment → Build-time Arguments: `NEXT_PUBLIC_BOT_API_URL` ni yangi bot manziliga o'zgartiring va Deploy.
4. `sayt/index.html` da `leadUrl` ni (`https://bot.YANGI-DOMEN/lead`) o'zgartirib push qiling.
5. BotFather → Menu Button URL'ini yangi Mini App manziliga o'zgartiring.
6. Bot `.env`/Environment da `ALLOWED_ORIGIN=*` qolsa, qo'shimcha o'zgartirish kerak emas.

## Eslatma: eski usul

`bot/deploy/setup-vps.sh` — botni Dokploy'siz, oddiy Ubuntu VPS'ga (systemd + Caddy) o'rnatish skripti. Hozir ishlatilmaydi,
zaxira variant sifatida qoldirilgan.
