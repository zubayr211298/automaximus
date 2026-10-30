"""Automaximus Telegram bot.

Faqat Python standart kutubxonasi ishlatiladi (Python 3.10+). Hech narsa o'rnatish shart emas.

Imkoniyatlar:
  * Mijoz: yozilish (xizmat -> mashina -> kun -> telefon -> tasdiq), narxlar, manzil,
    mening yozuvlarim, do'stni taklif qilish (referal havola), bog'lanish.
  * Admin chati: har bir so'rov karta bo'lib keladi; tugmalar bilan holatni o'zgartirish;
    kartaga rasm/video bilan javob berilsa — u mijozga "ish jarayonidan" deb yuboriladi.
  * Ish tugagach: mijozdan baho so'raladi; yaxshi baho -> sharh havolasi, yomon -> sabab adminga.
  * Takroriy xizmat eslatmalari (config.SERVICES dagi remind_days).
  * Reklama manbasini kuzatish: t.me/BOT?start=src_instagram kabi havolalar.
  * Sayt va Mini App uchun HTTP endpointlar: GET /services, POST /lead (channel: "site"/"miniapp").
  * Admin buyruqlari: /stat, /havola <manba>.
"""
from __future__ import annotations

import hashlib
import hmac
import html
import json
import logging
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import config

log = logging.getLogger("avtomaximus")
API = "https://api.telegram.org/bot{token}/{method}"

BTN_BOOK = "🗓 Yozilish"          # eski menyudan qolganlar uchun: barcha xizmatlar
BTN_SHOP = "🛞 Disk va balon"
BTN_DETAIL = "✨ Detailing"
BTN_PROMO = "🔥 Aksiya"
BTN_PRICES = "💰 Narxlar"
BTN_ADDR = "📍 Manzil va ish vaqti"
BTN_MY = "📋 Mening yozuvlarim"
BTN_REF = "🎁 Do‘stni taklif qilish"
BTN_CONTACT = "📞 Bog‘lanish"
BTN_SEND_PHONE = "📱 Raqamni yuborish"
BTN_CANCEL = "↩️ Bekor qilish"

STATUS_LABEL = {
    "new": "🆕 Yangi",
    "called": "📞 Bog‘lanildi",
    "done": "✅ Ish tugadi",
    "cancelled": "❌ Bekor qilindi",
}
SERVICE_NAMES = [s["name"] for s in config.SERVICES]
SERVICE_GROUP = {s["name"]: s.get("group", "detailing") for s in config.SERVICES}
BOOKING_STATES = ("svc", "car", "day", "day_text", "phone", "confirm")
BOT_USERNAME = ""
BROADCAST_ASYNC = True     # testlarda False — tarqatish shu oqimda bajariladi


def groups_of(services_text: str) -> list[str]:
    names = [s.strip() for s in (services_text or "").split(",") if s.strip()]
    return sorted({SERVICE_GROUP.get(n, "detailing") for n in names})


def now() -> datetime:
    return datetime.now(timezone.utc)


def esc(value) -> str:
    return html.escape(str(value or ""), quote=False)


# --------------------------------------------------------------------------
# Telegram API
# --------------------------------------------------------------------------
class TelegramError(Exception):
    def __init__(self, code: int, description: str):
        super().__init__(f"{code}: {description}")
        self.code = code
        self.description = description


def tg(method: str, **params):
    """Telegram Bot API chaqiruvi. Natijani qaytaradi yoki TelegramError ko'taradi."""
    data = json.dumps({k: v for k, v in params.items() if v is not None}).encode()
    req = urllib.request.Request(
        API.format(token=config.BOT_TOKEN, method=method),
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=70) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except Exception:
            raise TelegramError(e.code, str(e)) from None
    if not body.get("ok"):
        raise TelegramError(body.get("error_code", 0), body.get("description", ""))
    return body.get("result")


def safe_send(chat_id: int, text: str, **kw):
    """Xabar yuborish; mijoz botni bloklagan bo'lsa jim o'tib ketadi."""
    try:
        return tg("sendMessage", chat_id=chat_id, text=text, parse_mode="HTML",
                  disable_web_page_preview=True, **kw)
    except TelegramError as e:
        log.warning("sendMessage %s: %s", chat_id, e)
        return None


# --------------------------------------------------------------------------
# Ma'lumotlar bazasi (SQLite)
# --------------------------------------------------------------------------
class DB:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY, name TEXT, username TEXT, phone TEXT,
                source TEXT, referrer INTEGER, ref_rewarded INTEGER DEFAULT 0, created TEXT);
            CREATE TABLE IF NOT EXISTS sessions(
                user_id INTEGER PRIMARY KEY, state TEXT, data TEXT);
            CREATE TABLE IF NOT EXISTS bookings(
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, channel TEXT,
                name TEXT, phone TEXT, car TEXT, services TEXT, day TEXT, source TEXT,
                status TEXT DEFAULT 'new', rating INTEGER, admin_msg_id INTEGER,
                created TEXT, done_at TEXT);
            CREATE TABLE IF NOT EXISTS reminders(
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, booking_id INTEGER,
                service TEXT, due_at TEXT, sent INTEGER DEFAULT 0);
            """
        )
        # eski bazani yangilash: yangi ustunlar
        for table, col in (("sessions", "updated TEXT"), ("sessions", "nudged INTEGER DEFAULT 0"),
                           ("bookings", "sla_pinged INTEGER DEFAULT 0")):
            try:
                self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {col}")
            except sqlite3.OperationalError:
                pass
        self.conn.commit()

    def q(self, sql: str, args=(), one=False):
        with self.lock:
            cur = self.conn.execute(sql, args)
            rows = cur.fetchall()
            self.conn.commit()
            return (rows[0] if rows else None) if one else rows

    def x(self, sql: str, args=()) -> int:
        with self.lock:
            cur = self.conn.execute(sql, args)
            self.conn.commit()
            return cur.lastrowid

    # sessiya (yozilish bosqichlari)
    def get_session(self, uid: int):
        row = self.q("SELECT state, data FROM sessions WHERE user_id=?", (uid,), one=True)
        if not row:
            return None, {}
        return row["state"], json.loads(row["data"] or "{}")

    def set_session(self, uid: int, state, data: dict):
        if state is None:
            self.x("DELETE FROM sessions WHERE user_id=?", (uid,))
        else:
            self.x("INSERT INTO sessions(user_id,state,data,updated,nudged) VALUES(?,?,?,?,0) "
                   "ON CONFLICT(user_id) DO UPDATE SET state=excluded.state, data=excluded.data, "
                   "updated=excluded.updated, nudged=0",
                   (uid, state, json.dumps(data, ensure_ascii=False), now().isoformat()))


db: DB | None = None


# --------------------------------------------------------------------------
# Klaviaturalar
# --------------------------------------------------------------------------
def main_menu():
    return {"keyboard": [[{"text": BTN_SHOP}, {"text": BTN_DETAIL}],
                         [{"text": BTN_PRICES}, {"text": BTN_PROMO}],
                         [{"text": BTN_ADDR}, {"text": BTN_MY}],
                         [{"text": BTN_REF}, {"text": BTN_CONTACT}]],
            "resize_keyboard": True}


def book_buttons():
    return [[{"text": BTN_SHOP, "callback_data": "book:dokon"},
             {"text": BTN_DETAIL, "callback_data": "book:detailing"}]]


def services_kb(selected: list[str], group: str | None = None):
    rows = []
    for i, name in enumerate(SERVICE_NAMES):
        if group and SERVICE_GROUP[name] != group:
            continue
        mark = "✅ " if name in selected else "▫️ "
        rows.append([{"text": mark + name, "callback_data": f"svc:{i}"}])
    rows.append([{"text": "Davom etish ➡️", "callback_data": "svc_next"}])
    rows.append([{"text": "Bekor qilish", "callback_data": "cancel"}])
    return {"inline_keyboard": rows}


def day_kb():
    return {"inline_keyboard": [
        [{"text": "Bugun", "callback_data": "day:Bugun"}, {"text": "Ertaga", "callback_data": "day:Ertaga"}],
        [{"text": "Shu hafta", "callback_data": "day:Shu hafta"}],
        [{"text": "Boshqa kun — yozaman", "callback_data": "day_other"}],
    ]}


def phone_kb():
    return {"keyboard": [[{"text": BTN_SEND_PHONE, "request_contact": True}], [{"text": BTN_CANCEL}]],
            "resize_keyboard": True, "one_time_keyboard": True}


def confirm_kb():
    return {"inline_keyboard": [[{"text": "✅ Tasdiqlash", "callback_data": "confirm"},
                                 {"text": "❌ Bekor qilish", "callback_data": "cancel"}]]}


def admin_kb(bid: int, status: str):
    if status in ("done", "cancelled"):
        return {"inline_keyboard": []}
    row = []
    if status == "new":
        row.append({"text": "📞 Bog‘lanildi", "callback_data": f"b:called:{bid}"})
    row.append({"text": "✅ Ish tugadi", "callback_data": f"b:done:{bid}"})
    row.append({"text": "❌ Bekor", "callback_data": f"b:cancel:{bid}"})
    return {"inline_keyboard": [row]}


def rating_kb(bid: int):
    return {"inline_keyboard": [[{"text": "⭐" * n, "callback_data": f"r:{bid}:{n}"} for n in (1, 2, 3)],
                                [{"text": "⭐" * n, "callback_data": f"r:{bid}:{n}"} for n in (4, 5)]]}


# --------------------------------------------------------------------------
# Yordamchilar
# --------------------------------------------------------------------------
PHONE_RE = re.compile(r"\d")


def normalize_phone(text: str) -> str | None:
    digits = "".join(PHONE_RE.findall(text or ""))
    if len(digits) == 9:
        digits = "998" + digits
    if 9 <= len(digits) <= 15:
        return "+" + digits
    return None


def is_admin(uid: int) -> bool:
    return uid in config.ADMIN_IDS


def upsert_user(u: dict, payload: str = ""):
    uid = u["id"]
    name = " ".join(x for x in (u.get("first_name"), u.get("last_name")) if x)
    existing = db.q("SELECT id FROM users WHERE id=?", (uid,), one=True)
    if existing:
        db.x("UPDATE users SET name=?, username=? WHERE id=?", (name, u.get("username"), uid))
        return False
    source, referrer = None, None
    if payload.startswith("ref_") and payload[4:].isdigit() and int(payload[4:]) != uid:
        referrer = int(payload[4:])
        source = "referal"
    elif payload:
        # t.me/BOT?start=ig_bio yoki eski ko'rinish start=src_instagram
        raw = payload[4:] if payload.startswith("src_") else payload
        source = re.sub(r"[^a-zA-Z0-9_-]", "", raw)[:32] or None
    db.x("INSERT INTO users(id,name,username,source,referrer,created) VALUES(?,?,?,?,?,?)",
         (uid, name, u.get("username"), source, referrer, now().isoformat()))
    return True


def booking_card(b) -> str:
    who = esc(b["name"]) or "—"
    if b["user_id"]:
        user = db.q("SELECT username FROM users WHERE id=?", (b["user_id"],), one=True)
        if user and user["username"]:
            who += f" (@{esc(user['username'])})"
        else:
            who += f' (<a href="tg://user?id={b["user_id"]}">profil</a>)'
    channel = {"bot": "Telegram bot", "miniapp": "Mini App"}.get(b["channel"], "Sayt formasi")
    kind = " + ".join({"dokon": "🛞 Do‘kon", "detailing": "✨ Detailing"}[g] for g in groups_of(b["services"]))
    lines = [
        f"<b>So‘rov #{b['id']}</b> · {STATUS_LABEL.get(b['status'], b['status'])}"
        + (f" · {kind}" if kind else ""),
        f"👤 {who}",
        f"📱 {esc(b['phone'])}",
        f"🚗 {esc(b['car']) or '—'}",
        f"🛠 {esc(b['services']) or 'ko‘rikda aniqlanadi'}",
        f"🗓 {esc(b['day']) or '—'}",
        f"📥 {channel}" + (f" · manba: {esc(b['source'])}" if b["source"] else ""),
    ]
    if b["rating"]:
        lines.append(f"⭐ Baho: {b['rating']}/5")
    if b["channel"] == "bot" and b["status"] not in ("done", "cancelled"):
        lines.append("<i>Ish rasmini mijozga yuborish uchun shu xabarga rasm bilan javob bering.</i>")
    return "\n".join(lines)


def notify_admin(bid: int):
    b = db.q("SELECT * FROM bookings WHERE id=?", (bid,), one=True)
    if not config.ADMIN_CHAT_ID:
        log.warning("ADMIN_CHAT_ID sozlanmagan — so'rov #%s faqat bazaga yozildi", bid)
        return
    msg = safe_send(config.ADMIN_CHAT_ID, booking_card(b), reply_markup=admin_kb(bid, b["status"]))
    if msg:
        db.x("UPDATE bookings SET admin_msg_id=? WHERE id=?", (msg["message_id"], bid))


def refresh_admin_card(bid: int):
    b = db.q("SELECT * FROM bookings WHERE id=?", (bid,), one=True)
    if not b or not b["admin_msg_id"]:
        return
    try:
        tg("editMessageText", chat_id=config.ADMIN_CHAT_ID, message_id=b["admin_msg_id"],
           text=booking_card(b), parse_mode="HTML", reply_markup=admin_kb(bid, b["status"]))
    except TelegramError as e:
        if "not modified" not in e.description:
            log.warning("editMessageText: %s", e)


def create_booking(*, user_id, channel, name, phone, car, services, day, source) -> int:
    bid = db.x(
        "INSERT INTO bookings(user_id,channel,name,phone,car,services,day,source,created) "
        "VALUES(?,?,?,?,?,?,?,?,?)",
        (user_id, channel, name, phone, car, services, day, source, now().isoformat()))
    notify_admin(bid)
    return bid


# --------------------------------------------------------------------------
# Mijoz tomoni
# --------------------------------------------------------------------------
SVC_PROMPTS = {
    "dokon": "🛞 <b>Do‘kon</b>\n\nNima kerak? Bir nechtasini tanlashingiz mumkin. "
             "Disk va balonni o‘rnatib beramiz.",
    "detailing": "✨ <b>Detailing</b>\n\nQaysi xizmat kerak? Bir nechtasini tanlashingiz mumkin. "
                 "Bilmasangiz — <b>Davom etish</b>ni bosing, bepul ko‘rikda aniqlaymiz.",
    None: "Nima kerak? Bir nechtasini tanlashingiz mumkin. "
          "Bilmasangiz — <b>Davom etish</b>ni bosing, ko‘rikda aniqlaymiz.",
}
CAR_PROMPTS = {
    "dokon": "Mashinangiz rusumi va disk/balon o‘lchami?\n(masalan: <i>Malibu 2, R17</i> yoki <i>Cobalt, 185/75 R14</i>)\n"
             "O‘lchamni bilmasangiz — faqat rusumini yozing, o‘zimiz tanlab beramiz.",
    None: "Mashinangiz rusumi va yili? (masalan, Chevrolet Cobalt 2022)",
}


def start_booking(uid: int, chat_id: int, group: str | None = None):
    db.set_session(uid, "svc", {"services": [], "group": group})
    safe_send(chat_id, SVC_PROMPTS.get(group, SVC_PROMPTS[None]), reply_markup=services_kb([], group))


def send_prices(chat_id: int):
    parts = []
    for group in ("dokon", "detailing"):
        rows = "\n".join(f"• <b>{esc(s['name'])}</b> — {esc(s['price'])}"
                         for s in config.SERVICES if s.get("group", "detailing") == group)
        if rows:
            parts.append(f"<b>{esc(config.GROUP_TITLES.get(group, group))}</b>\n{rows}")
    safe_send(chat_id, "<b>Narxlar</b>\n\n" + "\n\n".join(parts) +
              "\n\nAniq narx mashina turiga qarab aytiladi. Narx yozib beriladi va keyin oshmaydi. "
              "Bir nechta xizmatni birga olsangiz — arzonroq.",
              reply_markup={"inline_keyboard": book_buttons()})


def send_promo(chat_id: int):
    if config.PROMO_TEXT:
        safe_send(chat_id, config.PROMO_TEXT, reply_markup={"inline_keyboard": book_buttons()})
    else:
        safe_send(chat_id, "Hozircha aksiya yo‘q. Botni o‘chirmang — yangi aksiyalar haqida "
                           "birinchi bo‘lib shu yerda xabar beramiz 🔔",
                  reply_markup={"inline_keyboard": book_buttons()})


def send_address(chat_id: int):
    text = f"📍 <b>Manzil:</b> {esc(config.ADDRESS)}\n🕘 <b>Ish vaqti:</b> {esc(config.WORK_HOURS)}\n📞 {esc(config.PHONE)}"
    kb = {"inline_keyboard": [[{"text": "🗺 Xaritada ochish", "url": config.MAP_URL}]]} if config.MAP_URL else None
    safe_send(chat_id, text, reply_markup=kb)


def send_contact(chat_id: int):
    rows = []
    if config.ADMIN_USERNAME:
        rows.append([{"text": "✍️ Admin bilan yozishish", "url": f"https://t.me/{config.ADMIN_USERNAME}"}])
    if config.INSTAGRAM_URL:
        rows.append([{"text": "Instagram", "url": config.INSTAGRAM_URL}])
    safe_send(chat_id, f"📞 Qo‘ng‘iroq qiling: <b>{esc(config.PHONE)}</b>",
              reply_markup={"inline_keyboard": rows} if rows else None)


def send_my_bookings(uid: int, chat_id: int):
    rows = db.q("SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,))
    if not rows:
        safe_send(chat_id, "Hozircha yozuvlaringiz yo‘q.", reply_markup={"inline_keyboard": book_buttons()})
        return
    lines = [f"#{b['id']} · {esc(b['services']) or 'ko‘rik'} · {STATUS_LABEL.get(b['status'])}" for b in rows]
    safe_send(chat_id, "<b>Oxirgi yozuvlaringiz</b>\n\n" + "\n".join(lines))


def send_referral(uid: int, chat_id: int):
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}" if BOT_USERNAME else "(bot nomi aniqlanmadi)"
    invited = db.q("SELECT COUNT(*) c FROM users WHERE referrer=?", (uid,), one=True)["c"]
    safe_send(chat_id,
              f"🎁 <b>Do‘stingizni taklif qiling</b>\n\nShu havolani do‘stingizga yuboring. "
              f"U shu havola orqali kelib xizmatdan foydalansa, sizga: <b>{esc(config.REFERRAL_BONUS)}</b>\n\n"
              f"{link}\n\nSiz taklif qilganlar: <b>{invited}</b>")


def handle_message(m: dict):
    uid = m["from"]["id"]
    chat_id = m["chat"]["id"]
    text = (m.get("text") or "").strip()

    # Admin: kartaga rasm/video bilan javob — mijozga yuboriladi
    if chat_id == config.ADMIN_CHAT_ID and m.get("reply_to_message") and handle_admin_reply(m):
        return
    if is_admin(uid) and text.startswith("/") and handle_admin_command(uid, chat_id, text, m):
        return
    if m["chat"].get("type") != "private":
        return

    if text.startswith("/start"):
        payload = text.split(maxsplit=1)[1] if " " in text else ""
        is_new = upsert_user(m["from"], payload)
        db.set_session(uid, None, {})
        hello = ("Assalomu alaykum! <b>Automaximus</b>ga xush kelibsiz — mashinangiz uchun hammasi bir joyda.\n\n"
                 "🛞 <b>Do‘kon:</b> disk, balon, chexol, polik va aksessuarlar — o‘rnatish bilan.\n"
                 "✨ <b>Detailing:</b> tonirovka, broniplyonka, polirovka, ximchistka, shumoizolyatsiya.\n\n"
                 "Hamyonbop narx, narx oldindan aytiladi va oshmaydi. Pastdagi tugmalardan birini tanlang 👇")
        safe_send(chat_id, hello if is_new else "Asosiy menyu 👇", reply_markup=main_menu())
        return
    upsert_user(m["from"])

    state, data = db.get_session(uid)

    if text == BTN_CANCEL:
        db.set_session(uid, None, {})
        safe_send(chat_id, "Bekor qilindi.", reply_markup=main_menu())
        return
    if text in (BTN_BOOK, BTN_SHOP, BTN_DETAIL):
        start_booking(uid, chat_id, {BTN_SHOP: "dokon", BTN_DETAIL: "detailing"}.get(text))
        return
    menu = {BTN_PRICES: lambda: send_prices(chat_id), BTN_PROMO: lambda: send_promo(chat_id),
            BTN_ADDR: lambda: send_address(chat_id), BTN_MY: lambda: send_my_bookings(uid, chat_id),
            BTN_REF: lambda: send_referral(uid, chat_id), BTN_CONTACT: lambda: send_contact(chat_id)}
    if text in menu and state not in ("phone",):
        menu[text]()
        return

    if state == "car":
        data["car"] = text[:80]
        db.set_session(uid, "day", data)
        safe_send(chat_id, "Qachon kelishingiz qulay?", reply_markup=day_kb())
        return
    if state == "day_text":
        data["day"] = text[:80]
        ask_phone(uid, chat_id, data)
        return
    if state == "phone":
        phone = normalize_phone(m["contact"]["phone_number"]) if m.get("contact") else normalize_phone(text)
        if not phone:
            safe_send(chat_id, "Raqamni to‘g‘ri yozing (masalan, +998 90 123 45 67) yoki tugmani bosing.",
                      reply_markup=phone_kb())
            return
        data["phone"] = phone
        db.x("UPDATE users SET phone=? WHERE id=?", (phone, uid))
        db.set_session(uid, "confirm", data)
        safe_send(chat_id, "Deyarli tayyor ✅", reply_markup={"remove_keyboard": True})
        safe_send(chat_id, summary_text(data), reply_markup=confirm_kb())
        return
    if state == "feedback":
        bid = data.get("booking_id")
        if config.ADMIN_CHAT_ID:
            safe_send(config.ADMIN_CHAT_ID, f"⚠️ <b>So‘rov #{bid} bo‘yicha norozilik</b>\n\n{esc(text)}")
        db.set_session(uid, None, {})
        safe_send(chat_id, "Rahmat, fikringizni rahbariyatga yetkazdik. Tez orada siz bilan bog‘lanamiz.",
                  reply_markup=main_menu())
        return

    safe_send(chat_id, "Pastdagi tugmalardan birini tanlang 👇", reply_markup=main_menu())


def ask_phone(uid: int, chat_id: int, data: dict):
    user = db.q("SELECT phone FROM users WHERE id=?", (uid,), one=True)
    db.set_session(uid, "phone", data)
    hint = f"\n\nOldingi raqamingiz: <b>{esc(user['phone'])}</b> — uni qayta yozishingiz mumkin." if user and user["phone"] else ""
    safe_send(chat_id, "Telefon raqamingizni yuboring — pastdagi tugmani bosing yoki yozing." + hint,
              reply_markup=phone_kb())


def ask_car(chat_id: int, data: dict):
    safe_send(chat_id, CAR_PROMPTS.get(data.get("group"), CAR_PROMPTS[None]),
              reply_markup={"inline_keyboard": [[{"text": "O‘tkazib yuborish", "callback_data": "car_skip"}]]})


def resume_booking(uid: int, chat_id: int, state: str, data: dict):
    """Chala qolgan yozilishni to'xtagan joyidan davom ettiradi."""
    db.set_session(uid, state, data)
    if state == "svc":
        group = data.get("group")
        safe_send(chat_id, SVC_PROMPTS.get(group, SVC_PROMPTS[None]),
                  reply_markup=services_kb(data.get("services") or [], group))
    elif state == "car":
        ask_car(chat_id, data)
    elif state in ("day", "day_text"):
        db.set_session(uid, "day", data)
        safe_send(chat_id, "Qachon kelishingiz qulay?", reply_markup=day_kb())
    elif state == "phone":
        ask_phone(uid, chat_id, data)
    elif state == "confirm":
        safe_send(chat_id, summary_text(data), reply_markup=confirm_kb())


def summary_text(d: dict) -> str:
    return ("<b>Tekshiring:</b>\n\n"
            f"🛠 {esc(', '.join(d.get('services') or [])) or 'ko‘rikda aniqlanadi'}\n"
            f"🚗 {esc(d.get('car')) or '—'}\n"
            f"🗓 {esc(d.get('day')) or '—'}\n"
            f"📱 {esc(d.get('phone'))}")


def handle_callback(c: dict):
    uid = c["from"]["id"]
    msg = c.get("message") or {}
    chat_id = msg.get("chat", {}).get("id", uid)
    data_str = c.get("data") or ""
    answer = ""
    upsert_user(c["from"])

    if data_str.startswith("b:"):
        answer = handle_admin_action(uid, data_str)
    elif data_str.startswith("r:"):
        answer = handle_rating(uid, chat_id, data_str)
    elif data_str == "book" or data_str.startswith("book:"):
        group = data_str[5:] if data_str.startswith("book:") else None
        start_booking(uid, chat_id, group if group in ("dokon", "detailing") else None)
    elif data_str in ("bc_yes", "bc_no"):
        answer = handle_broadcast_confirm(uid, chat_id, msg, data_str == "bc_yes")
    elif data_str == "resume":
        state, data = db.get_session(uid)
        if state in BOOKING_STATES:
            resume_booking(uid, chat_id, state, data)
        else:
            start_booking(uid, chat_id)
    else:
        state, data = db.get_session(uid)
        if data_str == "cancel":
            db.set_session(uid, None, {})
            edit_or_send(msg, chat_id, "Bekor qilindi.")
            safe_send(chat_id, "Asosiy menyu 👇", reply_markup=main_menu())
        elif state == "svc" and data_str.startswith("svc:"):
            idx = int(data_str[4:])
            if 0 <= idx < len(SERVICE_NAMES):
                name = SERVICE_NAMES[idx]
                sel = data.get("services", [])
                sel.remove(name) if name in sel else sel.append(name)
                data["services"] = sel
                db.set_session(uid, "svc", data)
                try:
                    tg("editMessageReplyMarkup", chat_id=chat_id, message_id=msg.get("message_id"),
                       reply_markup=services_kb(sel, data.get("group")))
                except TelegramError:
                    pass
        elif state == "svc" and data_str == "svc_next":
            db.set_session(uid, "car", data)
            ask_car(chat_id, data)
        elif state == "car" and data_str == "car_skip":
            db.set_session(uid, "day", data)
            safe_send(chat_id, "Qachon kelishingiz qulay?", reply_markup=day_kb())
        elif state == "day" and data_str.startswith("day:"):
            data["day"] = data_str[4:]
            ask_phone(uid, chat_id, data)
        elif state == "day" and data_str == "day_other":
            db.set_session(uid, "day_text", data)
            safe_send(chat_id, "Qaysi kun va soat qulay? Yozib yuboring.")
        elif state == "confirm" and data_str == "confirm":
            user = db.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
            create_booking(user_id=uid, channel="bot", name=user["name"], phone=data.get("phone"),
                           car=data.get("car"), services=", ".join(data.get("services") or []),
                           day=data.get("day"), source=user["source"])
            db.set_session(uid, None, {})
            edit_or_send(msg, chat_id, summary_text(data).replace("Tekshiring:", "So‘rov yuborildi ✅"))
            safe_send(chat_id, config.THANKS_TEXT, reply_markup=main_menu())
        else:
            answer = "Bu tugma eskirgan. Qaytadan boshlang."
    try:
        tg("answerCallbackQuery", callback_query_id=c["id"], text=answer or None)
    except TelegramError:
        pass


def edit_or_send(msg: dict, chat_id: int, text: str):
    try:
        tg("editMessageText", chat_id=chat_id, message_id=msg.get("message_id"), text=text, parse_mode="HTML")
    except TelegramError:
        safe_send(chat_id, text)


# --------------------------------------------------------------------------
# Admin tomoni
# --------------------------------------------------------------------------
def handle_admin_action(uid: int, data_str: str) -> str:
    if not is_admin(uid):
        return "Bu tugma faqat admin uchun."
    _, action, bid = data_str.split(":")
    bid = int(bid)
    b = db.q("SELECT * FROM bookings WHERE id=?", (bid,), one=True)
    if not b:
        return "So‘rov topilmadi."
    if b["status"] in ("done", "cancelled"):
        return "Bu so‘rov allaqachon yopilgan."
    if action == "called":
        db.x("UPDATE bookings SET status='called' WHERE id=?", (bid,))
    elif action == "cancel":
        db.x("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
    elif action == "done":
        db.x("UPDATE bookings SET status='done', done_at=? WHERE id=?", (now().isoformat(), bid))
        on_done(bid)
    refresh_admin_card(bid)
    return "Saqlandi"


def on_done(bid: int):
    b = db.q("SELECT * FROM bookings WHERE id=?", (bid,), one=True)
    if not b["user_id"]:
        return
    uid = b["user_id"]
    safe_send(uid, "✅ Mashinangiz tayyor! Automaximus’ni tanlaganingiz uchun rahmat.\n\n"
                   "Xizmatimizni qanday baholaysiz?", reply_markup=rating_kb(bid))
    # takroriy xizmat eslatmalari
    for s in config.SERVICES:
        if s["name"] in (b["services"] or "") and s.get("remind_days"):
            due = now() + timedelta(days=s["remind_days"])
            db.x("INSERT INTO reminders(user_id,booking_id,service,due_at) VALUES(?,?,?,?)",
                 (uid, bid, s["name"], due.isoformat()))
    # referal bonusi: taklif qilingan do'stning birinchi tugagan ishi
    user = db.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
    done_count = db.q("SELECT COUNT(*) c FROM bookings WHERE user_id=? AND status='done'", (uid,), one=True)["c"]
    if user and user["referrer"] and not user["ref_rewarded"] and done_count == 1:
        db.x("UPDATE users SET ref_rewarded=1 WHERE id=?", (uid,))
        safe_send(user["referrer"], f"🎉 Siz taklif qilgan do‘stingiz xizmatimizdan foydalandi!\n"
                                    f"Sizga: <b>{esc(config.REFERRAL_BONUS)}</b>. Kelganingizda shu xabarni ko‘rsating.")
        if config.ADMIN_CHAT_ID:
            safe_send(config.ADMIN_CHAT_ID, f"🎁 Referal bonusi: mijoz {user['referrer']} "
                                            f"(so‘rov #{bid} orqali). Bonus: {esc(config.REFERRAL_BONUS)}")


def handle_rating(uid: int, chat_id: int, data_str: str) -> str:
    _, bid, n = data_str.split(":")
    bid, n = int(bid), int(n)
    b = db.q("SELECT * FROM bookings WHERE id=? AND user_id=?", (bid, uid), one=True)
    if not b:
        return ""
    if b["rating"]:
        return "Bahoingiz allaqachon qabul qilingan."
    db.x("UPDATE bookings SET rating=? WHERE id=?", (n, bid))
    refresh_admin_card(bid)
    if n >= 4:
        rows = []
        if config.REVIEW_URL:
            rows.append([{"text": "✍️ Sharh qoldirish", "url": config.REVIEW_URL}])
        if config.INSTAGRAM_URL:
            rows.append([{"text": "Instagram", "url": config.INSTAGRAM_URL}])
        safe_send(chat_id, "Rahmat! 🙌 Agar qiyin bo‘lmasa, qisqa sharh qoldiring — "
                           "bu boshqa haydovchilarga tanlashda yordam beradi.",
                  reply_markup={"inline_keyboard": rows} if rows else None)
    else:
        db.set_session(uid, "feedback", {"booking_id": bid})
        safe_send(chat_id, "Kechirasiz, kutganingizdek bo‘lmabdi. Nima yoqmaganini yozib qoldiring — "
                           "albatta tuzatamiz.")
    return "Rahmat!"


def handle_admin_reply(m: dict) -> bool:
    """Admin so'rov kartasiga rasm/video bilan javob bersa — mijozga yuboradi. Ishlov berilsa True."""
    reply_id = m["reply_to_message"]["message_id"]
    b = db.q("SELECT * FROM bookings WHERE admin_msg_id=?", (reply_id,), one=True)
    if not b or not b["user_id"]:
        return False
    if not (m.get("photo") or m.get("video") or m.get("document")):
        return False
    try:
        tg("sendMessage", chat_id=b["user_id"], text=f"📸 Ish jarayonidan (so‘rov #{b['id']}):")
        tg("copyMessage", chat_id=b["user_id"], from_chat_id=m["chat"]["id"], message_id=m["message_id"])
        safe_send(m["chat"]["id"], "✅ Mijozga yuborildi.", reply_to_message_id=m["message_id"])
    except TelegramError as e:
        safe_send(m["chat"]["id"], f"Yuborib bo‘lmadi: {esc(e.description)}")
    return True


ADMIN_HELP = ("<b>Admin buyruqlari</b>\n\n"
              "/stat — statistika\n"
              "/havola ig_bio — reklama uchun kuzatuv havolasi\n"
              "/tarqat matn — hamma mijozlarga xabar (aksiya)\n"
              "Rasm yoki videoga javob qilib /tarqat — o‘sha rasmni tarqatadi\n\n"
              "So‘rov kartasiga rasm/video bilan javob bersangiz — mijozga boradi.")


def handle_admin_command(uid: int, chat_id: int, text: str, m: dict) -> bool:
    cmd = text.split(maxsplit=1)[0].split("@")[0].lower()
    arg = text.split(maxsplit=1)[1].strip() if " " in text.strip() else ""
    if cmd == "/stat":
        send_stats(chat_id)
    elif cmd == "/havola":
        name = re.sub(r"[^a-zA-Z0-9_-]", "", arg)[:32] or "instagram"
        safe_send(chat_id, f"Reklama havolasi (<b>{name}</b>):\nhttps://t.me/{BOT_USERNAME}?start={name}\n\n"
                           "Shu havola orqali kelganlar /stat da alohida ko‘rinadi.")
    elif cmd == "/tarqat":
        reply = m.get("reply_to_message")
        if reply:
            job = {"copy_from": reply["chat"]["id"] if reply.get("chat") else chat_id,
                   "message_id": reply["message_id"]}
            preview = "Javob qilingan xabar"
        elif arg:
            job = {"text": arg}
            preview = esc(arg)
        else:
            safe_send(chat_id, "Foydalanish: <code>/tarqat Aksiya matni</code> yoki rasmga javob qilib /tarqat")
            return True
        count = db.q("SELECT COUNT(*) c FROM users", one=True)["c"]
        db.set_session(uid, "bc", job)
        safe_send(chat_id, f"📣 <b>{count} ta mijozga yuboriladi:</b>\n\n{preview}\n\nTasdiqlaysizmi?",
                  reply_markup={"inline_keyboard": [[{"text": "✅ Yuborish", "callback_data": "bc_yes"},
                                                     {"text": "❌ Bekor", "callback_data": "bc_no"}]]})
    elif cmd in ("/admin", "/help"):
        safe_send(chat_id, ADMIN_HELP)
    else:
        return False
    return True


def handle_broadcast_confirm(uid: int, chat_id: int, msg: dict, yes: bool) -> str:
    if not is_admin(uid):
        return "Bu tugma faqat admin uchun."
    state, job = db.get_session(uid)
    db.set_session(uid, None, {})
    if state != "bc":
        return "Eskirgan."
    if not yes:
        edit_or_send(msg, chat_id, "Tarqatish bekor qilindi.")
        return "Bekor"
    edit_or_send(msg, chat_id, "📣 Tarqatish boshlandi…")
    if BROADCAST_ASYNC:
        threading.Thread(target=broadcast, args=(job, chat_id), daemon=True).start()
    else:
        broadcast(job, chat_id)
    return "Boshlandi"


def broadcast(job: dict, report_chat: int):
    users = [r["id"] for r in db.q("SELECT id FROM users")]
    ok = fail = 0
    for user_id in users:
        try:
            if "text" in job:
                tg("sendMessage", chat_id=user_id, text=job["text"], parse_mode="HTML",
                   reply_markup={"inline_keyboard": book_buttons()})
            else:
                tg("copyMessage", chat_id=user_id, from_chat_id=job["copy_from"], message_id=job["message_id"],
                   reply_markup={"inline_keyboard": book_buttons()})
            ok += 1
        except TelegramError:
            fail += 1          # botni bloklagan
        except Exception:
            fail += 1
            log.exception("broadcast")
        if BROADCAST_ASYNC:
            time.sleep(0.05)   # Telegram cheklovi: sekundiga ~30 xabar
    safe_send(report_chat, f"📣 Tarqatish tugadi: ✅ {ok} ta yetdi, ❌ {fail} ta yetmadi (botni bloklagan).")


def send_stats(chat_id: int):
    users = db.q("SELECT COUNT(*) c FROM users", one=True)["c"]
    by_src = db.q("SELECT COALESCE(source,'to‘g‘ridan-to‘g‘ri') s, COUNT(*) c FROM users GROUP BY s ORDER BY c DESC")
    by_status = {r["status"]: r["c"] for r in db.q("SELECT status, COUNT(*) c FROM bookings GROUP BY status")}
    by_channel = {r["channel"]: r["c"] for r in db.q("SELECT channel, COUNT(*) c FROM bookings GROUP BY channel")}
    rating = db.q("SELECT AVG(rating) a, COUNT(rating) c FROM bookings WHERE rating IS NOT NULL", one=True)
    repeat = db.q("SELECT COUNT(*) c FROM (SELECT user_id FROM bookings WHERE status='done' AND user_id IS NOT NULL "
                  "GROUP BY user_id HAVING COUNT(*)>=2)", one=True)["c"]
    kinds = {"dokon": 0, "detailing": 0}
    for r in db.q("SELECT services FROM bookings"):
        for g in groups_of(r["services"]):
            kinds[g] = kinds.get(g, 0) + 1
    total = sum(by_status.values())
    done = by_status.get("done", 0)
    conv = f"{done * 100 // total}%" if total else "—"
    src_lines = "\n".join(f"  • {esc(r['s'])}: {r['c']}" for r in by_src) or "  —"
    avg = f"{rating['a']:.1f} ({rating['c']} ta)" if rating["c"] else "—"
    safe_send(chat_id,
              f"<b>Statistika</b>\n\n👥 Bot foydalanuvchilari: <b>{users}</b>\n{src_lines}\n\n"
              f"📥 So‘rovlar: <b>{total}</b> (bot: {by_channel.get('bot', 0)}, sayt: {by_channel.get('site', 0)}, "
              f"mini app: {by_channel.get('miniapp', 0)})\n"
              f"  🛞 Do‘kon: {kinds['dokon']} · ✨ Detailing: {kinds['detailing']}\n"
              f"  🆕 {by_status.get('new', 0)} · 📞 {by_status.get('called', 0)} · ✅ {done} · ❌ {by_status.get('cancelled', 0)}\n"
              f"📈 So‘rovdan mijozga: <b>{conv}</b>\n⭐ O‘rtacha baho: <b>{avg}</b>\n"
              f"🔁 Qayta kelgan mijozlar: <b>{repeat}</b>")


# --------------------------------------------------------------------------
# Eslatmalar
# --------------------------------------------------------------------------
def process_reminders():
    due = db.q("SELECT * FROM reminders WHERE sent=0 AND due_at<=?", (now().isoformat(),))
    for r in due:
        text = config.REMINDER_TEXTS.get(r["service"], f"{r['service']} xizmatidan beri ancha vaqt o‘tdi.")
        sent = safe_send(r["user_id"], f"🔔 {esc(text)}",
                         reply_markup={"inline_keyboard": [[{"text": "🗓 Yozilish", "callback_data": "book"}]]})
        db.x("UPDATE reminders SET sent=? WHERE id=?", (1 if sent else 2, r["id"]))


def process_abandoned():
    """Yozilishni boshlab tugatmagan mijozga bitta eslatma; raqami bo'lsa adminga ham xabar."""
    cutoff = (now() - timedelta(hours=config.ABANDON_HOURS)).isoformat()
    marks = ",".join("?" * len(BOOKING_STATES))
    rows = db.q(f"SELECT * FROM sessions WHERE state IN ({marks}) AND COALESCE(nudged,0)=0 "
                f"AND updated IS NOT NULL AND updated<=?", (*BOOKING_STATES, cutoff))
    for s in rows:
        db.x("UPDATE sessions SET nudged=1 WHERE user_id=?", (s["user_id"],))
        data = json.loads(s["data"] or "{}")
        safe_send(s["user_id"], "Yozilishni oxiriga yetkazmadingiz 🙂 Davom ettiramizmi? "
                                "Bor-yo‘g‘i 1 daqiqa qoldi.",
                  reply_markup={"inline_keyboard": [[{"text": "▶️ Davom etish", "callback_data": "resume"},
                                                     {"text": "Yo‘q, rahmat", "callback_data": "cancel"}]]})
        if data.get("phone") and config.ADMIN_CHAT_ID:
            safe_send(config.ADMIN_CHAT_ID,
                      "⚠️ <b>Chala qolgan so‘rov</b> — mijoz tasdiqlamadi, qo‘ng‘iroq qilib ko‘ring:\n"
                      f"📱 {esc(data.get('phone'))}\n🛠 {esc(', '.join(data.get('services') or [])) or '—'}\n"
                      f"🚗 {esc(data.get('car')) or '—'}")


def process_sla():
    """Yangi so'rovga belgilangan vaqtda javob berilmasa — adminga eslatma."""
    cutoff = (now() - timedelta(minutes=config.ADMIN_SLA_MINUTES)).isoformat()
    rows = db.q("SELECT * FROM bookings WHERE status='new' AND COALESCE(sla_pinged,0)=0 AND created<=?", (cutoff,))
    for b in rows:
        db.x("UPDATE bookings SET sla_pinged=1 WHERE id=?", (b["id"],))
        if config.ADMIN_CHAT_ID:
            safe_send(config.ADMIN_CHAT_ID,
                      f"⏰ So‘rov #{b['id']} ga {config.ADMIN_SLA_MINUTES} daqiqadan beri javob berilmadi! "
                      f"Mijoz boshqa joyga ketmasidan qo‘ng‘iroq qiling: {esc(b['phone'])}",
                      reply_to_message_id=b["admin_msg_id"] or None)


def reminder_loop(stop: threading.Event):
    while not stop.wait(60):
        for job in (process_reminders, process_abandoned, process_sla):
            try:
                job()
            except Exception:
                log.exception("fon vazifasi %s", job.__name__)


# --------------------------------------------------------------------------
# Sayt formasi: POST /lead
# --------------------------------------------------------------------------
_rate: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def rate_ok(ip: str, limit: int = 5, window: int = 600) -> bool:
    t = time.time()
    with _rate_lock:
        hits = [h for h in _rate.get(ip, []) if t - h < window]
        if len(hits) >= limit:
            _rate[ip] = hits
            return False
        hits.append(t)
        _rate[ip] = hits
        return True


def validate_init_data(init_data: str) -> dict | None:
    """Telegram Mini App initData'sini HMAC bilan tekshiradi; to'g'ri bo'lsa foydalanuvchi dict'ini
    qaytaradi (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app).
    Bo'sh yoki noto'g'ri bo'lsa None — bunday holda so'rov user_id'siz, anonim qabul qilinadi."""
    if not init_data or not config.BOT_TOKEN:
        return None
    try:
        pairs = urllib.parse.parse_qsl(init_data, strict_parsing=True)
    except ValueError:
        return None
    data = dict(pairs)
    received_hash = data.pop("hash", None)
    if not received_hash:
        return None
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(b"WebAppData", config.BOT_TOKEN.encode(), hashlib.sha256).digest()
    computed_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hash, received_hash):
        return None
    try:
        return json.loads(data.get("user", "{}"))
    except ValueError:
        return {}


def accept_lead(payload: dict, ip: str = "") -> tuple[int, dict]:
    if payload.get("website"):              # honeypot: odam to'ldirmaydi, spam-bot to'ldiradi
        return 200, {"ok": True}
    if not rate_ok(ip or "?"):
        return 429, {"ok": False, "error": "Juda ko‘p so‘rov. Birozdan keyin urinib ko‘ring."}
    phone = normalize_phone(str(payload.get("phone", "")))
    name = str(payload.get("name", "")).strip()[:60]
    channel = "miniapp" if payload.get("channel") == "miniapp" else "site"

    user_id = None
    if channel == "miniapp":
        tg_user = validate_init_data(str(payload.get("initData", "")))
        if tg_user and tg_user.get("id"):
            user_id = tg_user["id"]
            upsert_user(tg_user)
            name = name or " ".join(x for x in (tg_user.get("first_name"), tg_user.get("last_name")) if x)

    if not phone or not name:
        return 400, {"ok": False, "error": "Ism va telefon raqam kerak."}
    services = payload.get("services") or []
    if isinstance(services, str):
        services = [s.strip() for s in services.split(",")]
    services = [s for s in services if s in SERVICE_NAMES]
    default_source = "miniapp" if channel == "miniapp" else "sayt"
    source = re.sub(r"[^a-zA-Z0-9_-]", "", str(payload.get("source", "")))[:32] or default_source
    bid = create_booking(user_id=user_id, channel=channel, name=name, phone=phone,
                         car=str(payload.get("car", "")).strip()[:80], services=", ".join(services),
                         day="", source=source)
    return 200, {"ok": True, "id": bid}


class LeadHandler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", config.ALLOWED_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        self._send(204, {})

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"ok": True})
        elif self.path == "/services":
            # Mini App shu yerdan xizmatlar/narxlarni oladi — config.py bitta manba bo'lib qoladi.
            self._send(200, {"services": config.SERVICES, "groupTitles": config.GROUP_TITLES})
        else:
            self._send(404, {"ok": False})

    def do_POST(self):
        if self.path != "/lead":
            self._send(404, {"ok": False})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > 10_000:
            self._send(413, {"ok": False})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode() or "{}")
        except (ValueError, UnicodeDecodeError):
            self._send(400, {"ok": False, "error": "JSON xato"})
            return
        ip = self.headers.get("X-Forwarded-For", self.client_address[0]).split(",")[0].strip()
        code, body = accept_lead(payload if isinstance(payload, dict) else {}, ip)
        self._send(code, body)

    def log_message(self, fmt, *args):
        log.info("http %s", fmt % args)


# --------------------------------------------------------------------------
# Ishga tushirish
# --------------------------------------------------------------------------
def handle_update(u: dict):
    try:
        if "message" in u:
            handle_message(u["message"])
        elif "callback_query" in u:
            handle_callback(u["callback_query"])
    except Exception:
        log.exception("update %s", u.get("update_id"))


def init(db_path: str | None = None):
    global db
    db = DB(db_path or config.DB_PATH)


def main():
    global BOT_USERNAME
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    if not config.BOT_TOKEN:
        raise SystemExit("BOT_TOKEN topilmadi. .env faylini to‘ldiring (README ga qarang).")
    init()
    me = tg("getMe")
    BOT_USERNAME = me["username"]
    log.info("Bot ishga tushdi: @%s", BOT_USERNAME)
    tg("setMyCommands", commands=[{"command": "start", "description": "Asosiy menyu"}])

    stop = threading.Event()
    threading.Thread(target=reminder_loop, args=(stop,), daemon=True).start()
    server = ThreadingHTTPServer((config.LEAD_HOST, config.LEAD_PORT), LeadHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    log.info("Sayt formasi uchun endpoint: http://%s:%s/lead", config.LEAD_HOST, config.LEAD_PORT)

    offset = 0
    while True:
        try:
            updates = tg("getUpdates", offset=offset, timeout=50,
                         allowed_updates=["message", "callback_query"])
            for u in updates:
                offset = u["update_id"] + 1
                handle_update(u)
        except TelegramError as e:
            log.error("getUpdates: %s", e)
            time.sleep(5)
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            log.warning("tarmoq: %s", e)
            time.sleep(3)
        except KeyboardInterrupt:
            stop.set()
            server.shutdown()
            break


if __name__ == "__main__":
    main()
