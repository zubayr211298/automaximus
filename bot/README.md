# Automaximus Telegram bot

Saytdagi so‘rovlarni sizga yetkazadi, mijozni yozadi, ish rasmlarini yuboradi, baho va sharh yig‘adi, takroriy xizmatga eslatadi va do‘stini olib kelganlarni hisoblaydi.

Faqat **Python 3.10+** kerak. Hech qanday kutubxona o‘rnatilmaydi.

---

## 1. Bot tuzilishi

### Mijoz ko‘radigan asosiy menyu

| Tugma | Nima qiladi |
|---|---|
| 🗓 Yozilish | Yozilish bosqichlari (pastda) |
| 💰 Narxlar | Xizmatlar va “dan … so‘m” narxlar + “Yozilish” tugmasi |
| 📍 Manzil va ish vaqti | Manzil, ish vaqti, telefon, xarita |
| 📋 Mening yozuvlarim | Oxirgi 5 ta so‘rov va holati |
| 🎁 Do‘stni taklif qilish | Shaxsiy referal havola + nechta odam taklif qilgani |
| 📞 Bog‘lanish | Telefon, admin bilan yozishish, Instagram |

### Yozilish bosqichlari

1. **Xizmat tanlash** — bir nechtasini belgilash mumkin (✅). Bilmasa — “Davom etish”.
2. **Mashina** — rusumi va yili (o‘tkazib yuborish mumkin).
3. **Kun** — Bugun / Ertaga / Shu hafta / Boshqa kun (yozadi).
4. **Telefon** — bitta tugma bilan yuboradi yoki yozadi (raqam tekshiriladi).
5. **Tasdiqlash** — xulosa ko‘rsatiladi → “✅ Tasdiqlash”.

Shundan so‘ng mijozga “Rahmat, tez orada qo‘ng‘iroq qilamiz” deyiladi, sizga esa karta keladi.

### Admin chatiga keladigan karta

```
So‘rov #12 · 🆕 Yangi
👤 Jasur (@jasur)
📱 +998901234567
🚗 Cobalt 2022
🛠 Tonirovka, Ximchistka
🗓 Ertaga
📥 Telegram bot · manba: instagram
[📞 Bog‘lanildi] [✅ Ish tugadi] [❌ Bekor]
```

- **📞 Bog‘lanildi** — holat o‘zgaradi.
- **Kartaga rasm yoki video bilan javob bering** (reply) → mijozga “📸 Ish jarayonidan” bo‘lib boradi. Saytdagi “ish rasmlari Telegramingizga” va’dasi shu.
- **✅ Ish tugadi** → mijozdan baho so‘raladi (⭐1–5), takroriy xizmat eslatmalari rejalashtiriladi, referal bonusi tekshiriladi.
- Saytdan kelgan so‘rovlar ham xuddi shunday karta bo‘lib keladi (“📥 Sayt formasi”).

### Baho va sharh

- ⭐4–5 → “Sharh qoldiring” tugmasi (Google/Instagram) — saytdagi “Mijozlar fikri” uchun real sharhlar yig‘iladi.
- ⭐1–3 → mijozdan sabab so‘raladi va sizga “⚠️ norozilik” bo‘lib keladi — muammoni sharh yozilishidan oldin hal qilasiz.

### Takroriy xizmat eslatmalari (`config.py` → `SERVICES`)

| Xizmat | Eslatma |
|---|---|
| Broniplyonka | 30 kundan keyin — bepul ko‘rikka taklif |
| Ximchistka | 90 kundan keyin |
| Polirovka | 120 kundan keyin |
| Tonirovka, Shumoizolyatsiya | yuborilmaydi |

Kunlar va matnlarni `config.py` da o‘zgartirasiz.

### Referal (do‘st olib kelish)

Har bir mijozga havola: `t.me/BOTINGIZ?start=ref_12345`. Do‘sti shu havola orqali kelib, birinchi ishi tugaganda — taklif qilganga bonus xabari va sizga eslatma keladi. Bonusni `config.py` dagi `REFERRAL_BONUS` da yozasiz.

### Reklama manbasini kuzatish

Adminda: `/havola instagram` → `t.me/BOTINGIZ?start=src_instagram`. Har bir reklama/stiker/banner uchun alohida havola qiling.
Saytda: `?utm_source=instagram` bilan kelganlar ham manba bilan yoziladi.

### Admin buyruqlari

- `/stat` — foydalanuvchilar (manba bo‘yicha), so‘rovlar (bot/sayt, holatlar), so‘rovdan mijozga foiz, o‘rtacha baho, qayta kelganlar.
- `/havola <nom>` — reklama uchun kuzatuv havolasi.

---

## 2. O‘rnatish

### 2.1. Bot yaratish
1. Telegramda **@BotFather** → `/newbot` → nom va username bering → **token** oling.
2. `/setuserpic` bilan logoni (Instagram avatari PNG) qo‘ying.

### 2.2. Admin chatini aniqlash
- Shaxsan qabul qilsangiz: **@userinfobot** ga yozing — u sizning ID raqamingizni beradi.
- Xodimlar bilan birga: guruh oching, botni qo‘shing, guruh ID sini oling (odatda `-100…` bilan boshlanadi).

### 2.3. `.env` faylini to‘ldirish
`.env.example` ni `.env` nomi bilan nusxalang va to‘ldiring:
```
BOT_TOKEN=123456:ABC...
ADMIN_CHAT_ID=-1001234567890
ADMIN_IDS=111111111,222222222
LEAD_PORT=8080
ALLOWED_ORIGIN=https://saytingiz.uz
```

### 2.4. `config.py` ni to‘ldirish
Telefon, manzil, ish vaqti, narxlar, `REVIEW_URL`, `INSTAGRAM_URL`, `ADMIN_USERNAME`, `REFERRAL_BONUS`.

### 2.5. Ishga tushirish
```
python3 bot.py
```
Server (VPS) da doimiy ishlashi uchun `avtomaximus-bot.service` faylidan foydalaning (ichida yo‘riqnoma bor).

### 2.6. Saytni botga ulash
Bot `http://SERVER:8080/lead` manzilini ochadi. Sayt HTTPS da bo‘lgani uchun bu manzil ham **HTTPS** bo‘lishi kerak — odatda Nginx yoki Caddy orqali domen ulanadi (masalan, `https://bot.saytingiz.uz/lead`).
Keyin kanvasdagi landing sahifada **Tweaks → Bot → leadUrl** ga shu manzilni yozing. Manzil yozilmaguncha forma faqat “Rahmat” ko‘rsatadi va so‘rovni hech qayerga yubormaydi.

---

## 3. Tekshirish
```
python3 test_bot.py
```
Telegramga ulanmasdan 14 ta test: yozilish, admin tugmalari, foto-hisobot, baho, eslatmalar, referal, statistika, sayt formasi, spam himoyasi.

## 4. Keyingi bosqich (ixtiyoriy)
Mini App: saytni bot ichida “Narx kalkulyatori va yozilish” oynasi qilib ochish, bonus kartasi.

## Yangi imkoniyatlar (do'kon + detailing versiyasi)

- **Menyu:** 🛞 Disk va balon · ✨ Detailing · 💰 Narxlar · 🔥 Aksiya · 📍 Manzil · 📋 Mening yozuvlarim · 🎁 Do'stni taklif qilish · 📞 Bog'lanish
- **Do'kon bo'limi:** Disk, Balon, Chexol va polik, Aksessuarlar. Mashina rusumi va disk/balon o'lchami so'raladi. Admin kartasida "🛞 Do'kon" yoki "✨ Detailing" belgisi chiqadi.
- **Chala qolgan yozilish:** mijoz yozilishni boshlab 2 soat ichida tugatmasa, unga bitta "Davom etamizmi?" xabari boradi. Raqamini qoldirgan bo'lsa, adminga ham "Chala qolgan so'rov" kartasi keladi. Vaqt: `config.ABANDON_HOURS`.
- **Javobsiz so'rov:** yangi so'rovga 30 daqiqa ichida "Bog'lanildi" bosilmasa, admin chatiga eslatma keladi. Vaqt: `config.ADMIN_SLA_MINUTES`.
- **Aksiya tarqatish:** `/tarqat matn` yoki rasm/videoga javob qilib `/tarqat`. Yuborishdan oldin tasdiqlash so'raladi, oxirida nechta mijozga yetgani aytiladi.
- **Aksiya tugmasi:** matnini `config.PROMO_TEXT` ga yozing.
- **Manba havolalari:** `/havola ig_bio` → `t.me/BOT?start=ig_bio`. Eski `src_...` havolalar ham ishlaydi.
- **Admin yordami:** `/admin`

Eski bazangiz bo'lsa ham ishlaydi: yangi ustunlar avtomatik qo'shiladi.
