"""Automaximus bot sozlamalari.

Maxfiy qiymatlar (token, admin ID) .env faylidan o'qiladi.
Xizmatlar, narxlar, eslatma muddatlari va matnlar shu faylda — kerak bo'lsa o'zgartiring.
"""
import os
from pathlib import Path


def _load_env(path: Path) -> None:
    """Oddiy .env o'quvchi: KALIT=qiymat qatorlarini os.environ ga yozadi."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


BASE_DIR = Path(__file__).resolve().parent
_load_env(BASE_DIR / ".env")

# --- Maxfiy sozlamalar (.env) ---------------------------------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
# So'rovlar keladigan chat: shaxsiy chat ID yoki guruh ID (guruh ID odatda -100 bilan boshlanadi)
ADMIN_CHAT_ID = int(os.environ.get("ADMIN_CHAT_ID", "0") or 0)
# /stat kabi admin buyruqlarini ishlata oladigan foydalanuvchilar (vergul bilan)
ADMIN_IDS = {int(x) for x in os.environ.get("ADMIN_IDS", "").replace(" ", "").split(",") if x}
# Sayt formasi uchun HTTP server
LEAD_HOST = os.environ.get("LEAD_HOST", "0.0.0.0")
LEAD_PORT = int(os.environ.get("LEAD_PORT", "8080"))
# Saytingiz manzili (CORS uchun). Bilmasangiz "*" qoldiring.
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")
DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "avtomaximus.db"))

# --- Studiya ma'lumotlari ---------------------------------------------------
STUDIO_NAME = "Automaximus"
PHONE = "+998 90 777 78 50"   # studiyaning yagona raqami
ADDRESS = "Fargʻona, Al Fargʻoniy koʻchasi, 108"
ADDRESS_RU = "Фергана, ул. Аль-Фаргони, 108"
WORK_HOURS = "08:00 – 20:00"
MAP_URL = "https://yandex.uz/maps/-/CXbBVMk7"                # Google/Yandex xarita havolasi (ixtiyoriy)
ADMIN_USERNAME = "murod_dasturchi"  # @ belgisiz — "Admin bilan yozishish" tugmasi uchun
REVIEW_URL = "https://yandex.uz/maps/org/automaximus/109758593206/reviews/"  # Yandex Maps sharhlari — yaxshi baho qo'yganlarga yuboriladi
INSTAGRAM_URL = "https://www.instagram.com/automaximus_shop/"

# --- Xizmatlar va mahsulotlar ---------------------------------------------------
# group: "detailing" — studiya xizmati, "dokon" — do'kondagi mahsulot (o'rnatish bilan)
# remind_days: ish tugagandan necha kun keyin mijozga eslatma yuborilsin (None — yuborilmaydi)
# Tartibni o'zgartirmang, oxiriga qo'shing (eski tugmalar raqam bo'yicha ishlaydi).
# name / price — o'zbekcha (name boshqa joylarda kalit sifatida ham ishlatiladi, o'zgartirmang);
# name_ru / price_ru — ruscha ko'rinish (bot va Mini App ruscha tilda shuni ko'rsatadi)
SERVICES = [
    {"name": "Tonirovka",        "group": "detailing", "price": "180 000 so‘mdan (orqa yon oynalar + sfera, 1,5 soat)", "remind_days": None,
     "name_ru": "Тонировка", "price_ru": "от 180 000 сум (задние боковые стёкла + сфера, 1,5 часа)"},
    {"name": "Broniplyonka",     "group": "detailing", "price": "2 900 000 so‘mdan (4 soat)", "remind_days": 30,
     "name_ru": "Бронепленка", "price_ru": "от 2 900 000 сум (4 часа)"},
    {"name": "Polirovka",        "group": "detailing", "price": "600 000 so‘mdan (4 soat)", "remind_days": 120,
     "name_ru": "Полировка", "price_ru": "от 600 000 сум (4 часа)"},
    {"name": "Ximchistka",       "group": "detailing", "price": "600 000 so‘mdan (salon, 4 soat)", "remind_days": 90,
     "name_ru": "Химчистка", "price_ru": "от 600 000 сум (салон, 4 часа)"},
    {"name": "Shumoizolyatsiya", "group": "detailing", "price": "600 000 so‘mdan (4 soat)", "remind_days": None,
     "name_ru": "Шумоизоляция", "price_ru": "от 600 000 сум (4 часа)"},
    {"name": "Disk",             "group": "dokon",     "price": "1 800 000 so‘mdan", "remind_days": None,
     "name_ru": "Диски", "price_ru": "от 1 800 000 сум"},
    {"name": "Balon",            "group": "dokon",     "price": "320 000 so‘mdan", "remind_days": 180,
     "name_ru": "Шины", "price_ru": "от 320 000 сум"},
    {"name": "Chexol va polik",  "group": "dokon",     "price": "chexol 450 000, polik 200 000 so‘mdan", "remind_days": None,
     "name_ru": "Чехлы и коврики", "price_ru": "чехлы от 450 000, коврики от 200 000 сум"},
    {"name": "Aksessuarlar",     "group": "dokon",     "price": "modelga qarab", "remind_days": None,
     "name_ru": "Аксессуары", "price_ru": "в зависимости от модели"},
]
GROUP_TITLES = {"dokon": "🛞 Do‘kon: disk, balon, aksessuar", "detailing": "✨ Detailing xizmatlari"}
GROUP_TITLES_RU = {"dokon": "🛞 Магазин: диски, шины, аксессуары", "detailing": "✨ Услуги детейлинга"}

# Hozirgi aksiya matni ("🔥 Aksiya" tugmasi). Bo'sh qolsa — "hozircha aksiya yo'q" deyiladi.
# PROMO_TEXT_RU bo'sh qolsa, ruscha tilda ham PROMO_TEXT ko'rsatiladi.
PROMO_TEXT = ("🎁 <b>Har yakshanba — sovg‘a!</b>\n\n"
              "Instagram sahifamizda (@automaximus_shop) izohda <b>«tonirovka»</b> so‘zini yozib qoldiring. "
              "Har yakshanba obunachilarimiz orasidan 5 kishiga orqa oynalarini tonirovka qilib beramiz.")
PROMO_TEXT_RU = ("🎁 <b>Каждое воскресенье — подарок!</b>\n\n"
                 "Напишите в комментариях на нашей странице в Instagram (@automaximus_shop) слово <b>«тонировка»</b>. "
                 "Каждое воскресенье среди подписчиков мы выбираем 5 человек и тонируем им задние стёкла.")
# Masalan:
# PROMO_TEXT = ("❄️ <b>Qishga tayyor</b> — 15-noyabrgacha!\n\nQishki balon olsangiz: o‘rnatish bilan, "
#               "fara polirovkasi — sovg‘a, ximchistka — 20% chegirma.")

# Yozilishni boshlab, tugatmagan mijozga necha soatdan keyin eslatma yuborilsin
ABANDON_HOURS = 2
# Yangi so'rovga admin necha daqiqa javob bermasa, admin chatiga eslatma kelsin
ADMIN_SLA_MINUTES = 30

REMINDER_TEXTS = {
    "Broniplyonka": "Broniplyonka qo‘yilganiga bir oy bo‘ldi. Bepul ko‘rikka keling — plyonka holatini tekshirib, maslahat beramiz.",
    "Polirovka": "Polirovkadan beri bir necha oy o‘tdi. Yaltirashni saqlash uchun himoya qatlamini yangilash vaqti keldi.",
    "Ximchistka": "Oxirgi ximchistkadan beri 3 oy o‘tdi. Salonni yana yangidek qilib beramizmi?",
    "Balon": "Balon almashtirilganiga yarim yil bo‘ldi. Mavsum almashyapti — balonlarni bepul tekshirib, "
             "kerak bo‘lsa almashtirib beramiz.",
}

REMINDER_TEXTS_RU = {
    "Broniplyonka": "Прошёл месяц с установки бронепленки. Приезжайте на бесплатный осмотр — проверим состояние плёнки и дадим советы.",
    "Polirovka": "С момента полировки прошло несколько месяцев. Пора обновить защитный слой, чтобы кузов продолжал блестеть.",
    "Ximchistka": "С последней химчистки прошло 3 месяца. Сделать салон снова как новый?",
    "Balon": "Прошло полгода с замены шин. Сезон меняется — бесплатно проверим шины и при необходимости заменим.",
}

# Do'stini taklif qilganlarga beriladigan bonus (o'zingiz belgilang)
#   REFERRAL_BONUS        — taklif qilgan mijozga, REFERRAL_FRIEND_BONUS — kelgan do'stga
#   REFERRAL_TIER_COUNT   — shuncha do'st xizmat olsa, taklif qilganga REFERRAL_TIER_BONUS beriladi
# Mukofot do'st birinchi xizmatini olib bo'lgach (admin "Bajarildi" bosganda) beriladi.
REFERRAL_BONUS = "50 000 so‘m chegirma (300 000 so‘mdan yuqori keyingi xizmatga)"
REFERRAL_BONUS_RU = "скидка 50 000 сум (на следующую услугу от 300 000 сум)"
REFERRAL_FRIEND_BONUS = REFERRAL_BONUS
REFERRAL_FRIEND_BONUS_RU = REFERRAL_BONUS_RU
REFERRAL_TIER_COUNT = 3
REFERRAL_TIER_BONUS = "orqa oynalarga tonirovka sovg‘a (180 000 so‘mlik)"
REFERRAL_TIER_BONUS_RU = "тонировка задних стёкол в подарок (на 180 000 сум)"

# Mijoz so'rov yuborgach ko'radigan matn
THANKS_TEXT = "Rahmat! So‘rovingiz qabul qilindi. Tez orada qo‘ng‘iroq qilib, aniq narxni aytamiz."
THANKS_TEXT_RU = "Спасибо! Ваша заявка принята. Скоро позвоним и назовём точную цену."
