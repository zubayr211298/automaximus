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
WORK_HOURS = "08:00 – 20:00"
MAP_URL = "https://yandex.uz/maps/-/CXbBVMk7"                # Google/Yandex xarita havolasi (ixtiyoriy)
ADMIN_USERNAME = ""         # masalan: avtomaximus_admin (@ belgisiz) — "Admin bilan yozishish" tugmasi uchun
REVIEW_URL = ""             # Google sharh havolasi — yaxshi baho qo'yganlarga yuboriladi
INSTAGRAM_URL = "https://www.instagram.com/automaximus_shop/"

# --- Xizmatlar va mahsulotlar ---------------------------------------------------
# group: "detailing" — studiya xizmati, "dokon" — do'kondagi mahsulot (o'rnatish bilan)
# remind_days: ish tugagandan necha kun keyin mijozga eslatma yuborilsin (None — yuborilmaydi)
# Tartibni o'zgartirmang, oxiriga qo'shing (eski tugmalar raqam bo'yicha ishlaydi).
SERVICES = [
    {"name": "Tonirovka",        "group": "detailing", "price": "180 000 so‘mdan (orqa yon oynalar + sfera, 1,5 soat)", "remind_days": None},
    {"name": "Broniplyonka",     "group": "detailing", "price": "2 900 000 so‘mdan (4 soat)", "remind_days": 30},
    {"name": "Polirovka",        "group": "detailing", "price": "600 000 so‘mdan (4 soat)", "remind_days": 120},
    {"name": "Ximchistka",       "group": "detailing", "price": "600 000 so‘mdan (salon, 4 soat)", "remind_days": 90},
    {"name": "Shumoizolyatsiya", "group": "detailing", "price": "600 000 so‘mdan (4 soat)", "remind_days": None},
    {"name": "Disk",             "group": "dokon",     "price": "1 800 000 so‘mdan", "remind_days": None},
    {"name": "Balon",            "group": "dokon",     "price": "320 000 so‘mdan", "remind_days": 180},
    {"name": "Chexol va polik",  "group": "dokon",     "price": "chexol 450 000, polik 200 000 so‘mdan", "remind_days": None},
    {"name": "Aksessuarlar",     "group": "dokon",     "price": "modelga qarab", "remind_days": None},
]
GROUP_TITLES = {"dokon": "🛞 Do‘kon: disk, balon, aksessuar", "detailing": "✨ Detailing xizmatlari"}

# Hozirgi aksiya matni ("🔥 Aksiya" tugmasi). Bo'sh qolsa — "hozircha aksiya yo'q" deyiladi.
PROMO_TEXT = ""
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

# Do'stini taklif qilganlarga beriladigan bonus (o'zingiz belgilang)
REFERRAL_BONUS = "[BONUS: masalan, keyingi xizmatga 10% chegirma]"

# Mijoz so'rov yuborgach ko'radigan matn
THANKS_TEXT = "Rahmat! So‘rovingiz qabul qilindi. Tez orada qo‘ng‘iroq qilib, aniq narxni aytamiz."
