# Avtomaximus — sayt va bot fayllari

## Papkalar
- sayt/        — tayyor landing sahifa (index.html), logotip sahifasi (logo.html) va ishga tushiruvchi fayl (support.js)
- dizayn-manba/ — Claude Design'dagi asl manba fayllari (tahrirlash uchun)
- bot/         — bot qanday ishlashi kerakligi va sayt formasi botga qanday ulanishi

## Saytni qanday ochish
Sayt fayllari bir-biriga bog'liq, shuning uchun index.html ni ikki marta bosib ochish har doim ham ishlamaydi.
1. Eng oson yo'l (internetga chiqarish): https://app.netlify.com/drop saytiga kiring va "sayt" papkasini sudrab tashlang. 1 daqiqada link beradi.
2. Kompyuterda ko'rish: "sayt" papkasida terminal oching va yozing:  python -m http.server 8000
   Keyin brauzerda: http://localhost:8000

## Ishga chiqarishdan oldin to'ldirish kerak (index.html ichida)
- [TELEFON RAQAM], [TELEFON]  -> +998 90 777 78 50
- [MANZIL], [ISH VAQTI]
- barcha [NARX], [MUDDAT], [SUMMA], [KAFOLAT MUDDATI]
- [INSTAGRAM HAVOLA] -> https://instagram.com/automaximus_shop
- [TELEGRAM HAVOLA]  -> bot linki, masalan https://t.me/<bot>?start=sayt
- mijoz fikrlari, rasm va videolar, "Narxingiz nega arzonroq?" javobi
- [BOT_SERVER_URL]/lead -> bot serverining haqiqiy manzili (bot/README.md ga qarang)

DIQQAT: [BOT_SERVER_URL] to'ldirilmaguncha forma "qabul qilindi" deydi, lekin so'rov hech qayerga bormaydi.

## Til almashtirgich (UZ / RU)
- `sayt/i18n.js` — saytdagi o'zbekcha matnlarni ruscha qiladi va headerga UZ/RU tugmasini qo'shadi. `index.html` ning `<head>` qismida `<script src="./i18n.js" defer></script>` qatori bo'lishi shart.
  **Dizayn canvas'dan saytni qayta eksport qilsangiz, shu qatorni qayta qo'shing.** Yangi matn qo'shsangiz, `i18n.js` dagi `PAIRS` ro'yxatiga `["o'zbekcha", "ruscha"]` juftligini qo'shing (tarjimasiz qolganlar brauzer konsolida `__i18nMissing()` bilan ko'rinadi).
- `mini-app/` — til do'koni `src/store/langStore.ts`, lug'at `src/lib/i18n.ts`.
- `bot/` — pastdagi `bot/README.md` ga qarang ("Tillar").
