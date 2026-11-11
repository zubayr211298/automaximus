"""Botni Telegramga ulanmasdan sinash: python3 test_bot.py"""
import json
import os
import tempfile
import threading
import unittest
import urllib.request
from datetime import timedelta
from http.server import ThreadingHTTPServer

import config
import bot

ADMIN = 1000
CLIENT = 2001
FRIEND = 2002


class FakeTG:
    def __init__(self):
        self.calls = []
        self.msg_id = 500

    def __call__(self, method, **params):
        self.calls.append((method, params))
        if method in ("sendMessage", "copyMessage"):
            self.msg_id += 1
            return {"message_id": self.msg_id, "chat": {"id": params.get("chat_id")}}
        if method == "getMe":
            return {"username": "avtomaximus_bot"}
        return True

    def sent_to(self, chat_id):
        return [p for m, p in self.calls if m == "sendMessage" and p.get("chat_id") == chat_id]

    def last_text(self, chat_id):
        msgs = self.sent_to(chat_id)
        return msgs[-1]["text"] if msgs else ""


def msg(uid, text=None, **extra):
    m = {"message_id": 1, "from": {"id": uid, "first_name": f"User{uid}", "username": f"u{uid}"},
         "chat": {"id": uid, "type": "private"}}
    if text is not None:
        m["text"] = text
    m.update(extra)
    return {"message": m}


def cb(uid, data, chat_id=None):
    return {"callback_query": {"id": "q", "from": {"id": uid, "first_name": f"User{uid}"},
                               "data": data, "message": {"message_id": 77, "chat": {"id": chat_id or uid}}}}


class BotFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
        config.ADMIN_CHAT_ID = ADMIN
        config.ADMIN_IDS = {ADMIN}
        bot.BOT_USERNAME = "avtomaximus_bot"
        bot.init(self.tmp)
        self.tg = FakeTG()
        bot.tg = self.tg
        bot._rate.clear()

    def tearDown(self):
        bot.db.conn.close()
        os.unlink(self.tmp)

    def book(self, uid, services=(0, 3), car="Cobalt 2022", day="day:Ertaga", phone="90 123 45 67"):
        bot.handle_update(msg(uid, bot.BTN_BOOK))
        for i in services:
            bot.handle_update(cb(uid, f"svc:{i}"))
        bot.handle_update(cb(uid, "svc_next"))
        bot.handle_update(msg(uid, car))
        bot.handle_update(cb(uid, day))
        bot.handle_update(msg(uid, phone))
        bot.handle_update(cb(uid, "confirm"))
        return bot.db.q("SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC", (uid,), one=True)

    def test_full_booking_flow_and_admin_card(self):
        bot.handle_update(msg(CLIENT, "/start src_instagram"))
        self.assertIn("xush kelibsiz", self.tg.last_text(CLIENT))
        b = self.book(CLIENT)
        self.assertEqual(b["services"], "Tonirovka, Ximchistka")
        self.assertEqual(b["phone"], "+998901234567")
        self.assertEqual(b["day"], "Ertaga")
        self.assertEqual(b["source"], "instagram")
        card = self.tg.last_text(ADMIN)
        self.assertIn(f"So‘rov #{b['id']}", card)
        self.assertIn("+998901234567", card)
        self.assertIsNotNone(b["admin_msg_id"])
        self.assertEqual(bot.db.get_session(CLIENT)[0], None)

    def test_toggle_service_off(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(CLIENT, bot.BTN_BOOK))
        bot.handle_update(cb(CLIENT, "svc:1"))
        bot.handle_update(cb(CLIENT, "svc:1"))
        self.assertEqual(bot.db.get_session(CLIENT)[1]["services"], [])

    def test_invalid_phone_reprompts(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(CLIENT, bot.BTN_BOOK))
        bot.handle_update(cb(CLIENT, "svc_next"))
        bot.handle_update(cb(CLIENT, "car_skip"))
        bot.handle_update(cb(CLIENT, "day_other"))
        bot.handle_update(msg(CLIENT, "Shanba 10:00"))
        bot.handle_update(msg(CLIENT, "abc"))
        self.assertEqual(bot.db.get_session(CLIENT)[0], "phone")
        self.assertIn("to‘g‘ri yozing", self.tg.last_text(CLIENT))
        contact = msg(CLIENT, None, contact={"phone_number": "998935554433"})
        bot.handle_update(contact)
        self.assertEqual(bot.db.get_session(CLIENT)[0], "confirm")

    def test_non_admin_cannot_press_admin_buttons(self):
        bot.handle_update(msg(CLIENT, "/start"))
        b = self.book(CLIENT)
        bot.handle_update(cb(CLIENT, f"b:done:{b['id']}"))
        self.assertEqual(bot.db.q("SELECT status FROM bookings WHERE id=?", (b["id"],), one=True)["status"], "new")

    def test_done_rating_reminders_and_referral(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(FRIEND, f"/start ref_{CLIENT}"))
        b = self.book(FRIEND, services=(2, 3))         # Polirovka, Ximchistka
        bot.handle_update(cb(ADMIN, f"b:called:{b['id']}", chat_id=ADMIN))
        bot.handle_update(cb(ADMIN, f"b:done:{b['id']}", chat_id=ADMIN))
        row = bot.db.q("SELECT status FROM bookings WHERE id=?", (b["id"],), one=True)
        self.assertEqual(row["status"], "done")
        self.assertTrue(any("baholaysiz" in p["text"] for p in self.tg.sent_to(FRIEND)))
        rem = bot.db.q("SELECT service FROM reminders WHERE user_id=? ORDER BY service", (FRIEND,))
        self.assertEqual([r["service"] for r in rem], ["Polirovka", "Ximchistka"])
        self.assertIn("taklif qilgan do‘stingiz", self.tg.last_text(CLIENT))
        # pressing done again is rejected
        bot.handle_update(cb(ADMIN, f"b:done:{b['id']}", chat_id=ADMIN))
        self.assertEqual(bot.db.q("SELECT ref_rewarded FROM users WHERE id=?", (FRIEND,), one=True)[0], 1)
        # low rating -> feedback forwarded to admin
        bot.handle_update(cb(FRIEND, f"r:{b['id']}:2"))
        bot.handle_update(msg(FRIEND, "Kech qoldi"))
        self.assertIn("norozilik", self.tg.last_text(ADMIN))
        self.assertIn("Kech qoldi", self.tg.last_text(ADMIN))
        # second rating ignored
        bot.handle_update(cb(FRIEND, f"r:{b['id']}:5"))
        self.assertEqual(bot.db.q("SELECT rating FROM bookings WHERE id=?", (b["id"],), one=True)[0], 2)

    def test_referral_double_sided_bonus_tier_and_button(self):
        bot.handle_update(msg(CLIENT, "/start"))
        friends = [2101, 2102, 2103]
        first_booking = None
        for n, f in enumerate(friends, start=1):
            bot.handle_update(msg(f, f"/start ref_{CLIENT}"))
            b = self.book(f, services=(0,))
            first_booking = first_booking or b
            bot.handle_update(cb(ADMIN, f"b:done:{b['id']}", chat_id=ADMIN))
            # do'st ham bonus oladi (ikki tomonlama)
            self.assertIn("Sizga ham", self.tg.last_text(f))
            self.assertIn("taklif qilgan do‘stingiz", self.tg.last_text(CLIENT) if n < 3 else
                          " ".join(p["text"] for p in self.tg.sent_to(CLIENT)))
            notes = [p["text"] for p in self.tg.sent_to(ADMIN) if "Referal" in p["text"]]
            self.assertIn(f"{n}/3", notes[-1])
            self.assertIn(f"id {f}", notes[-1])                       # admin do'stni ko'radi
            self.assertEqual("Qo‘shimcha sovg‘a" in notes[-1], n == 3)  # 3-do'stda polik sovg'a
        self.assertIn("3 ta do‘stingiz", self.tg.last_text(CLIENT))
        self.assertIn("tonirovka", self.tg.last_text(CLIENT))
        # yaxshi bahodan keyin "Do'st taklif qiling" tugmasi chiqadi va havolani yuboradi
        bot.handle_update(cb(friends[0], f"r:{first_booking['id']}:5"))
        kb = self.tg.sent_to(friends[0])[-1]["reply_markup"]["inline_keyboard"]
        self.assertIn("ref", [btn.get("callback_data") for row in kb for btn in row])
        bot.handle_update(cb(friends[0], "ref"))
        self.assertIn(f"start=ref_{friends[0]}", self.tg.last_text(friends[0]))
        bot.handle_update(cb(CLIENT, "ref"))
        self.assertIn("3 / 3", self.tg.last_text(CLIENT))
        # ruscha tilda ham ishlaydi
        bot.set_lang(CLIENT, "ru")
        bot.handle_update(cb(CLIENT, "ref"))
        self.assertIn("Пригласите друга", self.tg.last_text(CLIENT))

    def test_reminders_sent_when_due(self):
        bot.handle_update(msg(CLIENT, "/start"))
        b = self.book(CLIENT, services=(3,))
        bot.handle_update(cb(ADMIN, f"b:done:{b['id']}", chat_id=ADMIN))
        bot.process_reminders()
        self.assertEqual(bot.db.q("SELECT sent FROM reminders", one=True)[0], 0)
        past = (bot.now() - timedelta(minutes=1)).isoformat()
        bot.db.x("UPDATE reminders SET due_at=?", (past,))
        bot.process_reminders()
        self.assertEqual(bot.db.q("SELECT sent FROM reminders", one=True)[0], 1)
        self.assertIn("ximchistka", self.tg.last_text(CLIENT).lower())

    def test_photo_report_copied_to_client(self):
        bot.handle_update(msg(CLIENT, "/start"))
        b = self.book(CLIENT)
        reply = {"message": {"message_id": 900, "from": {"id": ADMIN, "first_name": "Admin"},
                             "chat": {"id": ADMIN, "type": "private"}, "photo": [{"file_id": "x"}],
                             "reply_to_message": {"message_id": b["admin_msg_id"]}}}
        bot.handle_update(reply)
        copies = [p for m, p in self.tg.calls if m == "copyMessage"]
        self.assertEqual(copies[-1]["chat_id"], CLIENT)
        self.assertEqual(copies[-1]["message_id"], 900)

    def test_stats_and_link_admin_only(self):
        bot.handle_update(msg(CLIENT, "/start src_banner"))
        self.book(CLIENT)
        bot.handle_update(msg(CLIENT, "/stat"))
        self.assertNotIn("Statistika", self.tg.last_text(CLIENT))
        bot.handle_update(msg(ADMIN, "/stat"))
        self.assertIn("Statistika", self.tg.last_text(ADMIN))
        self.assertIn("banner: 1", self.tg.last_text(ADMIN))
        bot.handle_update(msg(ADMIN, "/havola stiker"))
        self.assertIn("start=stiker", self.tg.last_text(ADMIN))

    def test_menu_buttons(self):
        bot.handle_update(msg(CLIENT, "/start"))
        for btn, needle in [(bot.BTN_PRICES, "Narxlar"), (bot.BTN_ADDR, "Manzil"), (bot.BTN_MY, "yozuvlaringiz"),
                            (bot.BTN_REF, "start=ref_2001"), (bot.BTN_CONTACT, "Qo‘ng‘iroq")]:
            bot.handle_update(msg(CLIENT, btn))
            self.assertIn(needle, self.tg.last_text(CLIENT), btn)

    def test_shop_flow_only_shop_items_and_card_label(self):
        bot.handle_update(msg(CLIENT, "/start ig_bio"))
        bot.handle_update(msg(CLIENT, bot.BTN_SHOP))
        kb = [p for m, p in self.tg.calls if m == "sendMessage" and p.get("chat_id") == CLIENT][-1]["reply_markup"]
        labels = " ".join(r[0]["text"] for r in kb["inline_keyboard"])
        self.assertIn("Disk", labels)
        self.assertNotIn("Tonirovka", labels)
        disk = bot.SERVICE_NAMES.index("Disk")
        bot.handle_update(cb(CLIENT, f"svc:{disk}"))
        bot.handle_update(cb(CLIENT, "svc_next"))
        self.assertIn("o‘lchami", self.tg.last_text(CLIENT))
        bot.handle_update(msg(CLIENT, "Malibu 2, R17"))
        bot.handle_update(cb(CLIENT, "day:Bugun"))
        bot.handle_update(msg(CLIENT, "901234567"))
        bot.handle_update(cb(CLIENT, "confirm"))
        b = bot.db.q("SELECT * FROM bookings WHERE user_id=?", (CLIENT,), one=True)
        self.assertEqual(b["services"], "Disk")
        self.assertEqual(b["source"], "ig_bio")
        self.assertIn("Do‘kon", self.tg.last_text(ADMIN))

    def test_prices_and_promo(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(CLIENT, bot.BTN_PRICES))
        self.assertIn("Disk", self.tg.last_text(CLIENT))
        self.assertIn("Tonirovka", self.tg.last_text(CLIENT))
        bot.handle_update(msg(CLIENT, bot.BTN_PROMO))
        shown = self.tg.last_text(CLIENT).lower()
        self.assertIn("yakshanba", shown)        # haqiqiy aksiya (Instagram o'yini) ko'rsatiladi
        self.assertIn("tonirovka", shown)
        old_uz, old_ru = config.PROMO_TEXT, config.PROMO_TEXT_RU
        try:
            config.PROMO_TEXT = config.PROMO_TEXT_RU = ""
            bot.handle_update(msg(CLIENT, bot.BTN_PROMO))
            self.assertIn("aksiya", self.tg.last_text(CLIENT).lower())   # bo'sh bo'lsa "aksiya yo'q" deyiladi
            config.PROMO_TEXT = "Qishga tayyor!"
            bot.handle_update(msg(CLIENT, bot.BTN_PROMO))
            self.assertEqual(self.tg.last_text(CLIENT), "Qishga tayyor!")
        finally:
            config.PROMO_TEXT, config.PROMO_TEXT_RU = old_uz, old_ru

    def test_abandoned_booking_nudged_once_and_admin_gets_phone(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(CLIENT, bot.BTN_DETAIL))
        bot.handle_update(cb(CLIENT, "svc:0"))
        bot.handle_update(cb(CLIENT, "svc_next"))
        bot.handle_update(cb(CLIENT, "car_skip"))
        bot.handle_update(cb(CLIENT, "day:Ertaga"))
        bot.handle_update(msg(CLIENT, "901234567"))          # confirm bosilmadi
        bot.process_abandoned()
        self.assertNotIn("oxiriga", self.tg.last_text(CLIENT))  # hali erta
        old = (bot.now() - timedelta(hours=3)).isoformat()
        bot.db.x("UPDATE sessions SET updated=?", (old,))
        bot.process_abandoned()
        self.assertIn("oxiriga", self.tg.last_text(CLIENT))
        self.assertIn("Chala qolgan", self.tg.last_text(ADMIN))
        n = len(self.tg.sent_to(CLIENT))
        bot.process_abandoned()
        self.assertEqual(len(self.tg.sent_to(CLIENT)), n)       # faqat bir marta
        bot.handle_update(cb(CLIENT, "resume"))
        self.assertIn("Tekshiring", self.tg.last_text(CLIENT))

    def test_admin_sla_ping(self):
        bot.handle_update(msg(CLIENT, "/start"))
        b = self.book(CLIENT)
        bot.process_sla()
        self.assertNotIn("javob berilmadi", self.tg.last_text(ADMIN))
        bot.db.x("UPDATE bookings SET created=?", ((bot.now() - timedelta(minutes=40)).isoformat(),))
        bot.process_sla()
        self.assertIn("javob berilmadi", self.tg.last_text(ADMIN))
        n = len(self.tg.sent_to(ADMIN))
        bot.process_sla()
        self.assertEqual(len(self.tg.sent_to(ADMIN)), n)

    def test_broadcast_needs_confirmation_and_admin(self):
        bot.BROADCAST_ASYNC = False
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(FRIEND, "/start"))
        bot.handle_update(msg(CLIENT, "/tarqat salom"))           # mijoz tarqata olmaydi
        self.assertNotIn("yuboriladi", self.tg.last_text(CLIENT))
        bot.handle_update(msg(ADMIN, "/tarqat Aksiya boshlandi"))
        self.assertIn("yuboriladi", self.tg.last_text(ADMIN))
        self.assertIn("xush kelibsiz", self.tg.last_text(FRIEND))   # hali yuborilmagan
        bot.handle_update(cb(ADMIN, "bc_yes", chat_id=ADMIN))
        self.assertEqual(self.tg.last_text(FRIEND), "Aksiya boshlandi")
        self.assertEqual(self.tg.last_text(CLIENT), "Aksiya boshlandi")
        self.assertIn("Tarqatish tugadi", self.tg.last_text(ADMIN))

    def test_html_is_escaped(self):
        bot.handle_update(msg(CLIENT, "/start"))
        b = self.book(CLIENT, car="<b>hack</b>")
        self.assertIn("&lt;b&gt;hack", self.tg.last_text(ADMIN))


class LeadEndpointTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
        config.ADMIN_CHAT_ID = ADMIN
        bot.init(self.tmp)
        self.tg = FakeTG()
        bot.tg = self.tg
        bot._rate.clear()
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), bot.LeadHandler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        bot.db.conn.close()
        os.unlink(self.tmp)

    def post(self, payload):
        req = urllib.request.Request(f"http://127.0.0.1:{self.port}/lead", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"}, method="POST")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        try:
            with opener.open(req, timeout=5) as r:
                return r.status, json.loads(r.read()), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read()), dict(e.headers)

    def test_valid_lead_creates_booking_and_notifies(self):
        code, body, headers = self.post({"name": "Jasur", "phone": "+998 90 111 22 33", "car": "Malibu",
                                         "services": ["Tonirovka", "Yo‘q xizmat"], "source": "sayt"})
        self.assertEqual(code, 200)
        self.assertTrue(body["ok"])
        self.assertEqual(headers.get("Access-Control-Allow-Origin"), config.ALLOWED_ORIGIN)
        b = bot.db.q("SELECT * FROM bookings", one=True)
        self.assertEqual(b["channel"], "site")
        self.assertEqual(b["services"], "Tonirovka")
        self.assertIn("Sayt formasi", self.tg.last_text(ADMIN))

    def test_missing_phone_rejected(self):
        code, body, _ = self.post({"name": "Jasur", "phone": "12"})
        self.assertEqual(code, 400)

    def test_honeypot_silently_dropped(self):
        code, body, _ = self.post({"name": "Bot", "phone": "901112233", "website": "spam.com"})
        self.assertEqual(code, 200)
        self.assertIsNone(bot.db.q("SELECT * FROM bookings", one=True))

    def test_rate_limit(self):
        codes = [self.post({"name": "A", "phone": "901112233"})[0] for _ in range(6)]
        self.assertEqual(codes[:5], [200] * 5)
        self.assertEqual(codes[5], 429)


def in_lang(update, code):
    """Telegram interfeys tilini (language_code) qo'shadi."""
    update["message"]["from"]["language_code"] = code
    return update


def keyboard_texts(params):
    kb = (params or {}).get("reply_markup") or {}
    return [b["text"] for row in kb.get("keyboard", []) for b in row]


class LanguageTest(unittest.TestCase):
    setUp = BotFlowTest.setUp
    tearDown = BotFlowTest.tearDown
    book = BotFlowTest.book

    def test_new_user_language_comes_from_telegram(self):
        bot.handle_update(in_lang(msg(CLIENT, "/start"), "ru"))
        self.assertIn("Добро пожаловать", self.tg.last_text(CLIENT))
        bot.handle_update(in_lang(msg(FRIEND, "/start"), "uz"))
        self.assertIn("xush kelibsiz", self.tg.last_text(FRIEND))
        bot.handle_update(msg(3003, "/start"))                       # language_code yo'q -> o'zbekcha
        self.assertIn("xush kelibsiz", self.tg.last_text(3003))

    def test_toggle_button_switches_both_ways(self):
        bot.handle_update(msg(CLIENT, "/start"))
        bot.handle_update(msg(CLIENT, "🌐 Русский"))
        self.assertIn("Язык переключён", self.tg.last_text(CLIENT))
        self.assertIn("💰 Цены", keyboard_texts(self.tg.sent_to(CLIENT)[-1]))
        self.assertEqual(bot.lang_of(CLIENT), "ru")
        bot.handle_update(msg(CLIENT, "🌐 O‘zbekcha"))
        self.assertIn("Til almashtirildi", self.tg.last_text(CLIENT))
        self.assertIn(bot.BTN_PRICES, keyboard_texts(self.tg.sent_to(CLIENT)[-1]))
        self.assertEqual(bot.lang_of(CLIENT), "uz")

    def test_russian_menu_buttons_and_prices(self):
        bot.handle_update(in_lang(msg(CLIENT, "/start"), "ru"))
        bot.handle_update(msg(CLIENT, "💰 Цены"))
        text = self.tg.last_text(CLIENT)
        self.assertIn("Цены", text)
        self.assertIn("Тонировка", text)
        self.assertIn("от 180 000 сум", text)
        self.assertIn("Магазин: диски, шины, аксессуары", text)
        bot.handle_update(msg(CLIENT, "📍 Адрес и время работы"))
        self.assertIn("Фергана", self.tg.last_text(CLIENT))
        bot.handle_update(msg(CLIENT, "🎁 Пригласить друга"))
        self.assertIn("start=ref_2001", self.tg.last_text(CLIENT))

    def test_russian_booking_stores_uzbek_keys(self):
        bot.handle_update(in_lang(msg(CLIENT, "/start"), "ru"))
        bot.handle_update(msg(CLIENT, "✨ Детейлинг"))
        self.assertIn("Детейлинг", self.tg.last_text(CLIENT))
        bot.handle_update(cb(CLIENT, "svc:0"))
        bot.handle_update(cb(CLIENT, "svc:3"))
        bot.handle_update(cb(CLIENT, "svc_next"))
        self.assertIn("Марка и год", self.tg.last_text(CLIENT))
        bot.handle_update(msg(CLIENT, "Cobalt 2022"))
        bot.handle_update(cb(CLIENT, "day:Ertaga"))
        bot.handle_update(msg(CLIENT, "90 123 45 67"))
        summary = self.tg.last_text(CLIENT)
        self.assertIn("Проверьте", summary)
        self.assertIn("Тонировка, Химчистка", summary)
        self.assertIn("Завтра", summary)
        bot.handle_update(cb(CLIENT, "confirm"))
        self.assertIn("Спасибо", self.tg.last_text(CLIENT))
        b = bot.db.q("SELECT * FROM bookings", one=True)
        self.assertEqual(b["services"], "Tonirovka, Ximchistka")      # bazada va adminga o'zbekcha kalit
        self.assertEqual(b["day"], "Ertaga")
        self.assertIn("So‘rov #", self.tg.last_text(ADMIN))            # admin kartasi o'zbekcha

    def test_start_payload_language_from_site(self):
        bot.handle_update(msg(CLIENT, "/start sayt__ru"))
        self.assertIn("Добро пожаловать", self.tg.last_text(CLIENT))
        self.assertEqual(bot.db.q("SELECT source FROM users WHERE id=?", (CLIENT,), one=True)["source"], "sayt")
        bot.handle_update(msg(CLIENT, "/start sayt__uz"))               # mavjud foydalanuvchi tilini ham almashtiradi
        self.assertEqual(bot.lang_of(CLIENT), "uz")
        self.assertEqual(bot.split_lang("ig_bio"), ("ig_bio", None))
        self.assertEqual(bot.split_lang("ref_5__ru"), ("ref_5", "ru"))

    def test_done_message_and_reminder_follow_user_language(self):
        bot.handle_update(in_lang(msg(CLIENT, "/start"), "ru"))
        b = self.book(CLIENT, services=(1,))                            # Broniplyonka (eslatma bor)
        bot.handle_update(cb(ADMIN, f"b:done:{b['id']}", chat_id=ADMIN))
        self.assertIn("Ваша машина готова", self.tg.last_text(CLIENT))
        past = (bot.now() - timedelta(minutes=1)).isoformat()
        bot.db.x("UPDATE reminders SET due_at=?", (past,))
        bot.process_reminders()
        self.assertIn("бронепленки", self.tg.last_text(CLIENT))

    def test_miniapp_lead_keeps_chosen_day(self):
        code, body = bot.accept_lead({"name": "Jasur", "phone": "901112233", "channel": "miniapp",
                                      "services": ["Tonirovka"], "day": "Ertaga"}, "1.2.3.4")
        self.assertEqual(code, 200)
        b = bot.db.q("SELECT * FROM bookings", one=True)
        self.assertEqual((b["channel"], b["day"]), ("miniapp", "Ertaga"))
        self.assertIn("Mini App", self.tg.last_text(ADMIN))

    def test_every_service_has_russian_text(self):
        for s in config.SERVICES:
            self.assertTrue(s.get("name_ru") and s.get("price_ru"), s["name"])
        self.assertEqual(set(config.GROUP_TITLES_RU), set(config.GROUP_TITLES))
        for service in config.REMINDER_TEXTS:
            self.assertIn(service, config.REMINDER_TEXTS_RU)


if __name__ == "__main__":
    unittest.main(verbosity=2)
