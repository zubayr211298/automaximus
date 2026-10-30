# Automaximus — joylashtirish (deployment) yo'riqnomasi

Hozirgi holat: VPS yo'q, BotFather tokeni yo'q, domen yo'q, Vercel hisobi bor. Shu tartibda
ketamiz — har bosqich oldingisiga bog'liq emas, birini qoldirib keyingisiga o'tishingiz mumkin.

## 0-bosqich: Telegram bot yaratish (5 daqiqa, faqat siz qila olasiz)

1. Telegram'da **@BotFather**ga yozing → `/newbot`.
2. Bot nomi (masalan `Automaximus`) va username (masalan `automaximus_bot`, oxiri `bot` bilan tugashi shart) bering.
3. BotFather sizga **token** beradi (`123456789:AAE...` ko'rinishida) — buni hech kimga yubormang, shu yerda ham chat orqali menga yuborishingiz shart emas, to'g'ridan-to'g'ri `.env` fayliga yozasiz (3-bosqich).
4. `/setuserpic` → Instagram avataringizni (logo) yuklang.
5. Admin chatini aniqlang:
   - Yolg'iz boshqarsangiz: **@userinfobot**ga yozing — u sizning ID raqamingizni beradi (`ADMIN_CHAT_ID` shu bo'ladi).
   - Jamoa bilan: guruh oching, botni qo'shing, guruh ID sini oling (`-100...` bilan boshlanadi).

## 1-bosqich: VPS olish

Har qanday Ubuntu 22.04/24.04 VPS ishlaydi, eng arzon tarif yetadi (1 CPU / 1GB RAM). Variantlar:

| Provayder | Taxminiy narx/oy | Izoh |
|---|---|---|
| **Hostinger** | ~$4-5 | Claude'da **Hostinger** plugini bor — VPS va domenni shu yerdan, OAuth orqali (parol menga berilmaydi) sozlashimiz mumkin. Pastda takliflarga qarang. |
| **Timeweb.cloud** | ~150 000 so'm | Rossiya/MDH uchun qulay, kartadan to'lash oson |
| **Hetzner** | ~€4 | Yevropada eng arzon va barqaror, lekin karta tasdiqlash biroz qattiqroq |

VPS olgach, sizga **IP manzil** va **root parol** (yoki SSH kalit) beriladi. O'shanda menga IP manzilni ayting — SSH orqali ulanib, qolgan hamma narsani (2-4 bosqich) men sozlab beraman.

## 2-bosqich: Domen (ixtiyoriy, lekin tavsiya etiladi)

HTTPS uchun domen kerak (Telegram Mini App va sayt formasi faqat HTTPS bilan ishlaydi).

- Domeningiz bo'lsa (masalan `automaximus.uz`) — shuni ishlatamiz: `bot.automaximus.uz` → bot API uchun.
- Hali yo'q bo'lsa: Hostinger/Cloudflare orqali `.uz` yoki `.com` domen sotib olish mumkin (~$10-15/yil).
- Tezroq va bepul sinab ko'rish uchun: domensiz ham `sslip.io` xizmati orqali avtomatik HTTPS olish mumkin (masalan VPS IP manzili `1.2.3.4` bo'lsa, `bot.1.2.3.4.sslip.io` manzili to'g'ridan-to'g'ri o'sha serverga yo'naladi, Caddy avtomatik SSL sertifikat oladi). Ishga tushirish uchun yetarli, keyin domenga o'tkazish mumkin.

## 3-bosqich: VPS'ni sozlash

IP manzil va kirish ma'lumotlari tayyor bo'lgach, menga ayting — quyidagilarni avtomatik bajaraman
(`bot/deploy/setup-vps.sh` skripti orqali, server ustida bir marta ishga tushiriladi):

1. Python3, pip, Caddy o'rnatish
2. `/opt/avtomaximus-bot` papkasini yaratish, `bot/` fayllarini shu yerga ko'chirish
3. `.env` faylini `.env.example` asosida yaratish — `BOT_TOKEN`, `ADMIN_CHAT_ID`, `ADMIN_IDS`ni siz beradigan qiymatlar bilan to'ldiramiz
4. `avtomaximus-bot.service`ni systemd'ga ulash (`systemctl enable --now`) — server qayta yoqilsa ham bot avtomatik ishga tushadi
5. Caddy orqali `https://bot.SIZNING-DOMENINGIZ` → `localhost:8080`ga yo'naltirish (SSL sertifikat avtomatik, bepul — Let's Encrypt)

Bajarilgach: `https://bot.SIZNING-DOMENINGIZ/health` ochilsa `{"ok":true}` chiqishi kerak — bot tirik.

## 4-bosqich: Mini App'ni Vercel'ga ulash

✅ **Bajarildi:** `mini-app/` Vercel'ga joylashtirilgan va jonli — **https://mini-app-pearl-five.vercel.app**
(hozircha xizmatlar ro'yxati bo'sh ko'rinadi, chunki bot backend hali ulanmagan — bu normal).

Qolgan ish (3-bosqich — VPS tayyor bo'lgach):

1. Vercel loyihasi sozlamalarida (vercel.com → `mini-app` loyihasi → Settings → Environment Variables) `NEXT_PUBLIC_BOT_API_URL=https://bot.SIZNING-DOMENINGIZ` qo'shiladi, so'ng **Redeploy** bosiladi.
2. BotFather'da: botingizga yozib `/mybots` → botni tanlang → **Bot Settings → Menu Button → Configure Menu Button** → `https://mini-app-pearl-five.vercel.app` manzilini kiriting.
3. Endi botni ochganda pastda "Menu" tugmasi — Mini App'ni ochadi.

## 5-bosqich: Saytni ulash

`sayt/support.js`dagi (yoki kanvasdagi "Tweaks → Bot → leadUrl") manzilni `https://bot.SIZNING-DOMENINGIZ/lead` qiling — shu yerdan boshlab sayt formasi haqiqiy so'rov yuboradi.

---

## Qisqacha: nima qachon kerak

| Bosqich | Kim bajaradi | Qachon |
|---|---|---|
| 0 — BotFather | Siz (Telegramda) | Hoziroq, 5 daqiqa |
| 1 — VPS sotib olish | Siz (to'lov kerak) | Hoziroq yoki keyinroq |
| 2 — Domen | Siz (to'lov, ixtiyoriy) | 1-bosqich bilan birga |
| 3 — VPS sozlash | Men (IP/token berilgach) | 0 va 1 tugagach |
| 4 — Mini App ulash | Men + Siz (BotFather'da 1 ta qadam) | 3 tugagach |
| 5 — Sayt ulash | Men | 3 tugagach |
