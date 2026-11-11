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
import texts
from texts import btn, btn_key, day_label, norm_lang, status_label, tr

log = logging.getLogger("avtomaximus")
API = "https://api.telegram.org/bot{token}/{method}"

# Tugma matnlari texts.py da, ikki tilda. Bu yerdagilar — o'zbekcha ko'rinishi (testlar va admin uchun).
BTN_BOOK = btn("uz", "book")          # eski menyudan qolganlar uchun: barcha xizmatlar
BTN_SHOP = btn("uz", "shop")
BTN_DETAIL = btn("uz", "detail")
BTN_PROMO = btn("uz", "promo")
BTN_PRICES = btn("uz", "prices")
BTN_ADDR = btn("uz", "addr")
BTN_MY = btn("uz", "my")
BTN_REF = btn("uz", "ref")
BTN_CONTACT = btn("uz", "contact")
BTN_SEND_PHONE = btn("uz", "phone")
BTN_CANCEL = btn("uz", "cancel")

STATUS_LABEL = texts.STATUS["uz"]      # admin kartasi o'zbekcha; mijozga status_label(status, lang)
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


def pick(name: str, lang: str):
    """config'dagi o'zbekcha qiymat yoki uning ruscha juftligi (NAME_RU). Ruscha bo'sh bo'lsa — o'zbekcha."""
    if lang == "ru":
        value = getattr(config, name + "_RU", None)
        if value:
            return value
    return getattr(config, name)


_SERVICE_BY_NAME = {s["name"]: s for s in config.SERVICES}


def svc_label(name: str, lang: str) -> str:
    """Xizmat nomi mijoz tilida. Bazada va tugma kalitlarida nom o'zbekcha qoladi."""
    s = _SERVICE_BY_NAME.get(name)
    return (s.get("name_ru") or name) if (lang == "ru" and s) else name


def svc_price(s: dict, lang: str) -> str:
    return (s.get("price_ru") or s["price"]) if lang == "ru" else s["price"]


def svc_list_label(services_text: str, lang: str) -> str:
    return ", ".join(svc_label(n.strip(), lang) for n in (services_text or "").split(",") if n.strip())


def split_lang(payload: str) -> tuple[str, str | None]:
    """/start parametridan til qo'shimchasini ajratadi: 'sayt__ru' -> ('sayt', 'ru')."""
    m = re.match(r"^(.*?)__(uz|ru)$", payload or "")
    return (m.group(1), m.group(2)) if m else (payload or "", None)


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
                           ("bookings", "sla_pinged INTEGER DEFAULT 0"), ("users", "lang TEXT")):
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


def lang_of(uid) -> str:
    """Foydalanuvchi tili (uz/ru). Saqlanmagan bo'lsa — o'zbekcha."""
    if not uid:
        return texts.DEFAULT_LANG
    row = db.q("SELECT lang FROM users WHERE id=?", (uid,), one=True)
    return norm_lang(row["lang"] if row else None)


def set_lang(uid: int, lang: str) -> None:
    db.x("UPDATE users SET lang=? WHERE id=?", (norm_lang(lang), uid))


# --------------------------------------------------------------------------
# Klaviaturalar
# --------------------------------------------------------------------------
def main_menu(lang: str = "uz"):
    return {"keyboard": [[{"text": btn(lang, "shop")}, {"text": btn(lang, "detail")}],
                         [{"text": btn(lang, "prices")}, {"text": btn(lang, "promo")}],
                         [{"text": btn(lang, "addr")}, {"text": btn(lang, "my")}],
                         [{"text": btn(lang, "ref")}, {"text": btn(lang, "contact")}],
                         [{"text": btn(lang, "lang")}]],
            "resize_keyboard": True}


def book_buttons(lang: str = "uz"):
    return [[{"text": btn(lang, "shop"), "callback_data": "book:dokon"},
             {"text": btn(lang, "detail"), "callback_data": "book:detailing"}]]


def services_kb(selected: list[str], group: str | None = None, lang: str = "uz"):
    rows = []
    for i, name in enumerate(SERVICE_NAMES):
        if group and SERVICE_GROUP[name] != group:
            continue
        mark = "✅ " if name in selected else "▫️ "
        rows.append([{"text": mark + svc_label(name, lang), "callback_data": f"svc:{i}"}])
    rows.append([{"text": tr(lang, "i_next"), "callback_data": "svc_next"}])
    rows.append([{"text": tr(lang, "i_cancel"), "callback_data": "cancel"}])
    return {"inline_keyboard": rows}


def day_kb(lang: str = "uz"):
    return {"inline_keyboard": [
        [{"text": day_label("Bugun", lang), "callback_data": "day:Bugun"},
         {"text": day_label("Ertaga", lang), "callback_data": "day:Ertaga"}],
        [{"text": day_label("Shu hafta", lang), "callback_data": "day:Shu hafta"}],
        [{"text": tr(lang, "i_other_day"), "callback_data": "day_other"}],
    ]}


def phone_kb(lang: str = "uz"):
    return {"keyboard": [[{"text": btn(lang, "phone"), "request_contact": True}], [{"text": btn(lang, "cancel")}]],
            "resize_keyboard": True, "one_time_keyboard": True}


def confirm_kb(lang: str = "uz"):
    return {"inline_keyboard": [[{"text": tr(lang, "i_confirm"), "callback_data": "confirm"},
                                 {"text": tr(lang, "i_confirm_cancel"), "callback_data": "cancel"}]]}


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


def upsert_user(u: dict, payload: str = "", lang: str | None = None):
    """Yangi foydalanuvchi bo'lsa True. Til: berilgan lang -> Telegram interfeys tili (ru) -> o'zbekcha."""
    uid = u["id"]
    name = " ".join(x for x in (u.get("first_name"), u.get("last_name")) if x)
    existing = db.q("SELECT id FROM users WHERE id=?", (uid,), one=True)
    if existing:
        db.x("UPDATE users SET name=?, username=? WHERE id=?", (name, u.get("username"), uid))
        return False
    if lang is None:
        lang = "ru" if str(u.get("language_code") or "").lower().startswith("ru") else "uz"
    source, referrer = None, None
    if payload.startswith("ref_") and payload[4:].isdigit() and int(payload[4:]) != uid:
        referrer = int(payload[4:])
        source = "referal"
    elif payload:
        # t.me/BOT?start=ig_bio yoki eski ko'rinish start=src_instagram
        raw = payload[4:] if payload.startswith("src_") else payload
        source = re.sub(r"[^a-zA-Z0-9_-]", "", raw)[:32] or None
    db.x("INSERT INTO users(id,name,username,source,referrer,created,lang) VALUES(?,?,?,?,?,?,?)",
         (uid, name, u.get("username"), source, referrer, now().isoformat(), norm_lang(lang)))
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
def svc_prompt(group: str | None, lang: str) -> str:
    return tr(lang, {"dokon": "svc_dokon", "detailing": "svc_detailing"}.get(group, "svc_all"))


def car_prompt(group: str | None, lang: str) -> str:
    return tr(lang, "car_dokon" if group == "dokon" else "car_all")


def start_booking(uid: int, chat_id: int, group: str | None = None):
    lang = lang_of(uid)
    db.set_session(uid, "svc", {"services": [], "group": group})
    safe_send(chat_id, svc_prompt(group, lang), reply_markup=services_kb([], group, lang))


def send_prices(chat_id: int, lang: str = "uz"):
    titles = pick("GROUP_TITLES", lang)
    parts = []
    for group in ("dokon", "detailing"):
        rows = "\n".join(f"• <b>{esc(svc_label(s['name'], lang))}</b> — {esc(svc_price(s, lang))}"
                         for s in config.SERVICES if s.get("group", "detailing") == group)
        if rows:
            parts.append(f"<b>{esc(titles.get(group, group))}</b>\n{rows}")
    safe_send(chat_id, f"<b>{tr(lang, 'prices_title')}</b>\n\n" + "\n\n".join(parts) + tr(lang, "prices_footer"),
              reply_markup={"inline_keyboard": book_buttons(lang)})


def send_promo(chat_id: int, lang: str = "uz"):
    promo = pick("PROMO_TEXT", lang)
    safe_send(chat_id, promo or tr(lang, "promo_none"), reply_markup={"inline_keyboard": book_buttons(lang)})


def send_address(chat_id: int, lang: str = "uz"):
    text = tr(lang, "addr", addr=esc(pick("ADDRESS", lang)), hours=esc(config.WORK_HOURS), phone=esc(config.PHONE))
    kb = {"inline_keyboard": [[{"text": tr(lang, "map_btn"), "url": config.MAP_URL}]]} if config.MAP_URL else None
    safe_send(chat_id, text, reply_markup=kb)


def send_contact(chat_id: int, lang: str = "uz"):
    rows = []
    if config.ADMIN_USERNAME:
        rows.append([{"text": tr(lang, "contact_admin_btn"), "url": f"https://t.me/{config.ADMIN_USERNAME}"}])
    if config.INSTAGRAM_URL:
        rows.append([{"text": "Instagram", "url": config.INSTAGRAM_URL}])
    safe_send(chat_id, tr(lang, "contact", phone=esc(config.PHONE)),
              reply_markup={"inline_keyboard": rows} if rows else None)


def send_my_bookings(uid: int, chat_id: int):
    lang = lang_of(uid)
    rows = db.q("SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC LIMIT 5", (uid,))
    if not rows:
        safe_send(chat_id, tr(lang, "my_none"), reply_markup={"inline_keyboard": book_buttons(lang)})
        return
    lines = [f"#{b['id']} · {esc(svc_list_label(b['services'], lang)) or tr(lang, 'my_row_fallback')} · "
             f"{status_label(b['status'], lang)}" for b in rows]
    safe_send(chat_id, tr(lang, "my_title") + "\n\n" + "\n".join(lines))


def send_referral(uid: int, chat_id: int):
    lang = lang_of(uid)
    link = f"https://t.me/{BOT_USERNAME}?start=ref_{uid}" if BOT_USERNAME else tr(lang, "ref_nolink")
    invited = db.q("SELECT COUNT(*) c FROM users WHERE referrer=?", (uid,), one=True)["c"]
    served = db.q("SELECT COUNT(*) c FROM users WHERE referrer=? AND ref_rewarded=1", (uid,), one=True)["c"]
    safe_send(chat_id, tr(lang, "ref", bonus=esc(pick("REFERRAL_BONUS", lang)), link=link, n=invited,
                          done=served, tier_n=config.REFERRAL_TIER_COUNT,
                          tier=esc(pick("REFERRAL_TIER_BONUS", lang))))


def toggle_lang(uid: int, chat_id: int):
    new = "ru" if lang_of(uid) == "uz" else "uz"
    set_lang(uid, new)
    safe_send(chat_id, tr(new, "lang_switched"), reply_markup=main_menu(new))


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
        payload, plang = split_lang(payload)       # sayt: t.me/BOT?start=sayt__ru -> til ham o'rnatiladi
        is_new = upsert_user(m["from"], payload, plang)
        if plang and not is_new:
            set_lang(uid, plang)
        lang = lang_of(uid)
        db.set_session(uid, None, {})
        safe_send(chat_id, tr(lang, "hello_new") if is_new else tr(lang, "menu_main"), reply_markup=main_menu(lang))
        return
    upsert_user(m["from"])
    lang = lang_of(uid)

    state, data = db.get_session(uid)
    key = btn_key(text)                            # tugma qaysi tilda bosilgan bo'lsa ham taniladi

    if key == "cancel":
        db.set_session(uid, None, {})
        safe_send(chat_id, tr(lang, "cancelled"), reply_markup=main_menu(lang))
        return
    if key == "lang":
        toggle_lang(uid, chat_id)
        return
    if key in ("book", "shop", "detail"):
        start_booking(uid, chat_id, {"shop": "dokon", "detail": "detailing"}.get(key))
        return
    menu = {"prices": lambda: send_prices(chat_id, lang), "promo": lambda: send_promo(chat_id, lang),
            "addr": lambda: send_address(chat_id, lang), "my": lambda: send_my_bookings(uid, chat_id),
            "ref": lambda: send_referral(uid, chat_id), "contact": lambda: send_contact(chat_id, lang)}
    if key in menu and state not in ("phone",):
        menu[key]()
        return

    if state == "car":
        data["car"] = text[:80]
        db.set_session(uid, "day", data)
        safe_send(chat_id, tr(lang, "when"), reply_markup=day_kb(lang))
        return
    if state == "day_text":
        data["day"] = text[:80]
        ask_phone(uid, chat_id, data)
        return
    if state == "phone":
        phone = normalize_phone(m["contact"]["phone_number"]) if m.get("contact") else normalize_phone(text)
        if not phone:
            safe_send(chat_id, tr(lang, "phone_bad"), reply_markup=phone_kb(lang))
            return
        data["phone"] = phone
        db.x("UPDATE users SET phone=? WHERE id=?", (phone, uid))
        db.set_session(uid, "confirm", data)
        safe_send(chat_id, tr(lang, "almost"), reply_markup={"remove_keyboard": True})
        safe_send(chat_id, summary_text(data, lang), reply_markup=confirm_kb(lang))
        return
    if state == "feedback":
        bid = data.get("booking_id")
        if config.ADMIN_CHAT_ID:
            safe_send(config.ADMIN_CHAT_ID, f"⚠️ <b>So‘rov #{bid} bo‘yicha norozilik</b>\n\n{esc(text)}")
        db.set_session(uid, None, {})
        safe_send(chat_id, tr(lang, "feedback_thanks"), reply_markup=main_menu(lang))
        return

    safe_send(chat_id, tr(lang, "pick_button"), reply_markup=main_menu(lang))


def ask_phone(uid: int, chat_id: int, data: dict):
    lang = lang_of(uid)
    user = db.q("SELECT phone FROM users WHERE id=?", (uid,), one=True)
    db.set_session(uid, "phone", data)
    hint = tr(lang, "ask_phone_hint", phone=esc(user["phone"])) if user and user["phone"] else ""
    safe_send(chat_id, tr(lang, "ask_phone") + hint, reply_markup=phone_kb(lang))


def ask_car(chat_id: int, data: dict, lang: str = "uz"):
    safe_send(chat_id, car_prompt(data.get("group"), lang),
              reply_markup={"inline_keyboard": [[{"text": tr(lang, "i_skip"), "callback_data": "car_skip"}]]})


def resume_booking(uid: int, chat_id: int, state: str, data: dict):
    """Chala qolgan yozilishni to'xtagan joyidan davom ettiradi."""
    lang = lang_of(uid)
    db.set_session(uid, state, data)
    if state == "svc":
        group = data.get("group")
        safe_send(chat_id, svc_prompt(group, lang),
                  reply_markup=services_kb(data.get("services") or [], group, lang))
    elif state == "car":
        ask_car(chat_id, data, lang)
    elif state in ("day", "day_text"):
        db.set_session(uid, "day", data)
        safe_send(chat_id, tr(lang, "when"), reply_markup=day_kb(lang))
    elif state == "phone":
        ask_phone(uid, chat_id, data)
    elif state == "confirm":
        safe_send(chat_id, summary_text(data, lang), reply_markup=confirm_kb(lang))


def summary_text(d: dict, lang: str = "uz", title: str = "sum_title") -> str:
    services = ", ".join(svc_label(n, lang) for n in (d.get("services") or []))
    return (f"<b>{tr(lang, title)}</b>\n\n"
            f"🛠 {esc(services) or tr(lang, 'tbd')}\n"
            f"🚗 {esc(d.get('car')) or '—'}\n"
            f"🗓 {esc(day_label(d.get('day') or '', lang)) or '—'}\n"
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
    elif data_str == "ref":
        send_referral(uid, chat_id)
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
        lang = lang_of(uid)
        if data_str == "cancel":
            db.set_session(uid, None, {})
            edit_or_send(msg, chat_id, tr(lang, "cancelled"))
            safe_send(chat_id, tr(lang, "menu_main"), reply_markup=main_menu(lang))
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
                       reply_markup=services_kb(sel, data.get("group"), lang))
                except TelegramError:
                    pass
        elif state == "svc" and data_str == "svc_next":
            db.set_session(uid, "car", data)
            ask_car(chat_id, data, lang)
        elif state == "car" and data_str == "car_skip":
            db.set_session(uid, "day", data)
            safe_send(chat_id, tr(lang, "when"), reply_markup=day_kb(lang))
        elif state == "day" and data_str.startswith("day:"):
            data["day"] = data_str[4:]
            ask_phone(uid, chat_id, data)
        elif state == "day" and data_str == "day_other":
            db.set_session(uid, "day_text", data)
            safe_send(chat_id, tr(lang, "when_other"))
        elif state == "confirm" and data_str == "confirm":
            user = db.q("SELECT * FROM users WHERE id=?", (uid,), one=True)
            create_booking(user_id=uid, channel="bot", name=user["name"], phone=data.get("phone"),
                           car=data.get("car"), services=", ".join(data.get("services") or []),
                           day=data.get("day"), source=user["source"])
            db.set_session(uid, None, {})
            edit_or_send(msg, chat_id, summary_text(data, lang, "sum_sent"))
            safe_send(chat_id, pick("THANKS_TEXT", lang), reply_markup=main_menu(lang))
        else:
            answer = tr(lang, "stale")
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
    safe_send(uid, tr(lang_of(uid), "done_msg"), reply_markup=rating_kb(bid))
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
        ref_id = user["referrer"]
        rl, fl = lang_of(ref_id), lang_of(uid)
        # ikki tomonlama bonus: taklif qilgan ham, kelgan do'st ham oladi
        safe_send(ref_id, tr(rl, "ref_bonus_msg", bonus=esc(pick("REFERRAL_BONUS", rl))))
        safe_send(uid, tr(fl, "ref_friend_msg", bonus=esc(pick("REFERRAL_FRIEND_BONUS", fl))))
        served = db.q("SELECT COUNT(*) c FROM users WHERE referrer=? AND ref_rewarded=1", (ref_id,), one=True)["c"]
        tier_hit = config.REFERRAL_TIER_COUNT and served == config.REFERRAL_TIER_COUNT
        if tier_hit:
            safe_send(ref_id, tr(rl, "ref_tier_msg", n=served, tier=esc(pick("REFERRAL_TIER_BONUS", rl))))
        if config.ADMIN_CHAT_ID:
            referrer = db.q("SELECT name, username FROM users WHERE id=?", (ref_id,), one=True)
            ref_label = f"{esc(referrer['name'] if referrer else '')} (id {ref_id})"
            friend_label = f"{esc(user['name'])} (id {uid}, {esc(b['phone'] or '—')})"
            note = (f"🎁 <b>Referal</b>: {ref_label} taklif qilgan {friend_label} birinchi xizmatni oldi "
                    f"(so‘rov #{bid}).\nIkkalasiga: {esc(config.REFERRAL_BONUS)}\n"
                    f"Taklif qilganning xizmat olgan do‘stlari: {served}/{config.REFERRAL_TIER_COUNT}")
            if tier_hit:
                note += f"\n🏆 Qo‘shimcha sovg‘a: {esc(config.REFERRAL_TIER_BONUS)}"
            safe_send(config.ADMIN_CHAT_ID, note)


def handle_rating(uid: int, chat_id: int, data_str: str) -> str:
    _, bid, n = data_str.split(":")
    bid, n = int(bid), int(n)
    b = db.q("SELECT * FROM bookings WHERE id=? AND user_id=?", (bid, uid), one=True)
    if not b:
        return ""
    lang = lang_of(uid)
    if b["rating"]:
        return tr(lang, "rated_already")
    db.x("UPDATE bookings SET rating=? WHERE id=?", (n, bid))
    refresh_admin_card(bid)
    if n >= 4:
        rows = []
        if config.REVIEW_URL:
            rows.append([{"text": tr(lang, "review_btn"), "url": config.REVIEW_URL}])
        if config.INSTAGRAM_URL:
            rows.append([{"text": "Instagram", "url": config.INSTAGRAM_URL}])
        # mijoz xursand bo'lgan payt — do'st taklif qilishning eng yaxshi vaqti
        rows.append([{"text": tr(lang, "i_ref"), "callback_data": "ref"}])
        safe_send(chat_id, tr(lang, "rated_good"), reply_markup={"inline_keyboard": rows})
    else:
        db.set_session(uid, "feedback", {"booking_id": bid})
        safe_send(chat_id, tr(lang, "rated_bad"))
    return tr(lang, "thanks_short")


def handle_admin_reply(m: dict) -> bool:
    """Admin so'rov kartasiga rasm/video bilan javob bersa — mijozga yuboradi. Ishlov berilsa True."""
    reply_id = m["reply_to_message"]["message_id"]
    b = db.q("SELECT * FROM bookings WHERE admin_msg_id=?", (reply_id,), one=True)
    if not b or not b["user_id"]:
        return False
    if not (m.get("photo") or m.get("video") or m.get("document")):
        return False
    try:
        tg("sendMessage", chat_id=b["user_id"], text=tr(lang_of(b["user_id"]), "photo_from_work", id=b["id"]))
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
    users = [(r["id"], norm_lang(r["lang"])) for r in db.q("SELECT id, lang FROM users")]
    ok = fail = 0
    for user_id, ulang in users:        # matn aksiyani admin yozadi, "Yozilish" tugmalari esa mijoz tilida
        try:
            if "text" in job:
                tg("sendMessage", chat_id=user_id, text=job["text"], parse_mode="HTML",
                   reply_markup={"inline_keyboard": book_buttons(ulang)})
            else:
                tg("copyMessage", chat_id=user_id, from_chat_id=job["copy_from"], message_id=job["message_id"],
                   reply_markup={"inline_keyboard": book_buttons(ulang)})
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
        lang = lang_of(r["user_id"])
        default = tr(lang, "reminder_default", service=esc(svc_label(r["service"], lang)))
        text = pick("REMINDER_TEXTS", lang).get(r["service"], default)
        sent = safe_send(r["user_id"], f"🔔 {esc(text)}",
                         reply_markup={"inline_keyboard": [[{"text": btn(lang, "book"), "callback_data": "book"}]]})
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
        lang = lang_of(s["user_id"])
        safe_send(s["user_id"], tr(lang, "abandoned"),
                  reply_markup={"inline_keyboard": [[{"text": tr(lang, "i_resume"), "callback_data": "resume"},
                                                     {"text": tr(lang, "i_no_thanks"), "callback_data": "cancel"}]]})
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
                         day=str(payload.get("day", "")).strip()[:80], source=source)
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
            self._send(200, {"services": config.SERVICES, "groupTitles": config.GROUP_TITLES,
                             "groupTitlesRu": config.GROUP_TITLES_RU})
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
    tg("setMyCommands", commands=[{"command": "start", "description": "Главное меню"}], language_code="ru")

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
