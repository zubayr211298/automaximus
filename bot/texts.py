"""Mijozga ko'rinadigan barcha bot matnlari: o'zbekcha (uz) va ruscha (ru).

Admin chatidagi kartalar va buyruqlar (/stat, /tarqat ...) faqat o'zbekcha — ular ishlatilmaydi bu yerda.
Yangi matn qo'shsangiz, ikkala tilga ham yozing. Ruscha topilmasa, o'zbekcha ko'rsatiladi.
"""
from __future__ import annotations

LANGS = ("uz", "ru")
DEFAULT_LANG = "uz"

T: dict[str, dict[str, str]] = {
    "uz": {
        "hello_new": (
            "Assalomu alaykum! <b>Automaximus</b>ga xush kelibsiz — mashinangiz uchun hammasi bir joyda.\n\n"
            "🛞 <b>Do‘kon:</b> disk, balon, chexol, polik va aksessuarlar — o‘rnatish bilan.\n"
            "✨ <b>Detailing:</b> tonirovka, broniplyonka, polirovka, ximchistka, shumoizolyatsiya.\n\n"
            "Hamyonbop narx, narx oldindan aytiladi va oshmaydi. Pastdagi tugmalardan birini tanlang 👇"),
        "menu_main": "Asosiy menyu 👇",
        "pick_button": "Pastdagi tugmalardan birini tanlang 👇",
        "cancelled": "Bekor qilindi.",
        "stale": "Bu tugma eskirgan. Qaytadan boshlang.",
        "lang_switched": "Til almashtirildi: O‘zbekcha ✅",
        "svc_dokon": ("🛞 <b>Do‘kon</b>\n\nNima kerak? Bir nechtasini tanlashingiz mumkin. "
                      "Disk va balonni o‘rnatib beramiz."),
        "svc_detailing": ("✨ <b>Detailing</b>\n\nQaysi xizmat kerak? Bir nechtasini tanlashingiz mumkin. "
                          "Bilmasangiz — <b>Davom etish</b>ni bosing, bepul ko‘rikda aniqlaymiz."),
        "svc_all": ("Nima kerak? Bir nechtasini tanlashingiz mumkin. "
                    "Bilmasangiz — <b>Davom etish</b>ni bosing, ko‘rikda aniqlaymiz."),
        "car_dokon": ("Mashinangiz rusumi va disk/balon o‘lchami?\n"
                      "(masalan: <i>Malibu 2, R17</i> yoki <i>Cobalt, 185/75 R14</i>)\n"
                      "O‘lchamni bilmasangiz — faqat rusumini yozing, o‘zimiz tanlab beramiz."),
        "car_all": "Mashinangiz rusumi va yili? (masalan, Chevrolet Cobalt 2022)",
        "when": "Qachon kelishingiz qulay?",
        "when_other": "Qaysi kun va soat qulay? Yozib yuboring.",
        "ask_phone": "Telefon raqamingizni yuboring — pastdagi tugmani bosing yoki yozing.",
        "ask_phone_hint": "\n\nOldingi raqamingiz: <b>{phone}</b> — uni qayta yozishingiz mumkin.",
        "phone_bad": "Raqamni to‘g‘ri yozing (masalan, +998 90 123 45 67) yoki tugmani bosing.",
        "almost": "Deyarli tayyor ✅",
        "sum_title": "Tekshiring:",
        "sum_sent": "So‘rov yuborildi ✅",
        "tbd": "ko‘rikda aniqlanadi",
        "prices_title": "Narxlar",
        "prices_footer": ("\n\nAniq narx mashina turiga qarab aytiladi. Narx yozib beriladi va keyin oshmaydi. "
                          "Bir nechta xizmatni birga olsangiz — arzonroq."),
        "promo_none": ("Hozircha aksiya yo‘q. Botni o‘chirmang — yangi aksiyalar haqida "
                       "birinchi bo‘lib shu yerda xabar beramiz 🔔"),
        "addr": "📍 <b>Manzil:</b> {addr}\n🕘 <b>Ish vaqti:</b> {hours}\n📞 {phone}",
        "map_btn": "🗺 Xaritada ochish",
        "contact": "📞 Qo‘ng‘iroq qiling: <b>{phone}</b>",
        "contact_admin_btn": "✍️ Admin bilan yozishish",
        "my_none": "Hozircha yozuvlaringiz yo‘q.",
        "my_title": "<b>Oxirgi yozuvlaringiz</b>",
        "my_row_fallback": "ko‘rik",
        "ref": ("🎁 <b>Do‘stingizni taklif qiling</b>\n\nShu havolani do‘stingizga yuboring. "
                "U shu havola orqali kelib birinchi xizmatini olsa, <b>ikkalangizga</b>: {bonus}\n"
                "{tier_n} ta do‘st olib kelsangiz — {tier}.\n\n"
                "{link}\n\nTaklif qilganlaringiz: <b>{n}</b>\nXizmat olganlar: <b>{done} / {tier_n}</b>"),
        "ref_friend_msg": ("🎁 Birinchi xizmatingiz uchun rahmat. Sizga ham: <b>{bonus}</b>\n"
                           "Kelganingizda shu xabarni ko‘rsating."),
        "ref_tier_msg": ("🏆 {n} ta do‘stingiz xizmatimizdan foydalandi. Sovg‘a: <b>{tier}</b>\n"
                         "Kelganingizda shu xabarni ko‘rsating."),
        "i_ref": "🎁 Do‘stni taklif qiling",
        "ref_nolink": "(bot nomi aniqlanmadi)",
        "feedback_thanks": "Rahmat, fikringizni rahbariyatga yetkazdik. Tez orada siz bilan bog‘lanamiz.",
        "done_msg": ("✅ Mashinangiz tayyor! Automaximus’ni tanlaganingiz uchun rahmat.\n\n"
                     "Xizmatimizni qanday baholaysiz?"),
        "ref_bonus_msg": ("🎉 Siz taklif qilgan do‘stingiz xizmatimizdan foydalandi!\n"
                          "Sizga: <b>{bonus}</b>. Kelganingizda shu xabarni ko‘rsating."),
        "rated_already": "Bahoingiz allaqachon qabul qilingan.",
        "rated_good": ("Rahmat! 🙌 Agar qiyin bo‘lmasa, qisqa sharh qoldiring — "
                       "bu boshqa haydovchilarga tanlashda yordam beradi."),
        "rated_bad": ("Kechirasiz, kutganingizdek bo‘lmabdi. Nima yoqmaganini yozib qoldiring — "
                      "albatta tuzatamiz."),
        "review_btn": "✍️ Sharh qoldirish",
        "thanks_short": "Rahmat!",
        "photo_from_work": "📸 Ish jarayonidan (so‘rov #{id}):",
        "reminder_default": "{service} xizmatidan beri ancha vaqt o‘tdi.",
        "abandoned": "Yozilishni oxiriga yetkazmadingiz 🙂 Davom ettiramizmi? Bor-yo‘g‘i 1 daqiqa qoldi.",
        # tugmalar (oddiy klaviatura)
        "b_book": "🗓 Yozilish",
        "b_shop": "🛞 Disk va balon",
        "b_detail": "✨ Detailing",
        "b_promo": "🔥 Aksiya",
        "b_prices": "💰 Narxlar",
        "b_addr": "📍 Manzil va ish vaqti",
        "b_my": "📋 Mening yozuvlarim",
        "b_ref": "🎁 Do‘stni taklif qilish",
        "b_contact": "📞 Bog‘lanish",
        "b_phone": "📱 Raqamni yuborish",
        "b_cancel": "↩️ Bekor qilish",
        "b_lang": "🌐 Русский",
        # inline tugmalar
        "i_next": "Davom etish ➡️",
        "i_cancel": "Bekor qilish",
        "i_skip": "O‘tkazib yuborish",
        "i_other_day": "Boshqa kun — yozaman",
        "i_confirm": "✅ Tasdiqlash",
        "i_confirm_cancel": "❌ Bekor qilish",
        "i_resume": "▶️ Davom etish",
        "i_no_thanks": "Yo‘q, rahmat",
    },
    "ru": {
        "hello_new": (
            "Здравствуйте! Добро пожаловать в <b>Automaximus</b> — всё для вашей машины в одном месте.\n\n"
            "🛞 <b>Магазин:</b> диски, шины, чехлы, коврики и аксессуары — с установкой.\n"
            "✨ <b>Детейлинг:</b> тонировка, бронепленка, полировка, химчистка, шумоизоляция.\n\n"
            "Доступные цены, цена называется заранее и не растёт. Выберите кнопку ниже 👇"),
        "menu_main": "Главное меню 👇",
        "pick_button": "Выберите одну из кнопок ниже 👇",
        "cancelled": "Отменено.",
        "stale": "Эта кнопка устарела. Начните заново.",
        "lang_switched": "Язык переключён: Русский ✅",
        "svc_dokon": ("🛞 <b>Магазин</b>\n\nЧто нужно? Можно выбрать несколько позиций. "
                      "Диски и шины установим."),
        "svc_detailing": ("✨ <b>Детейлинг</b>\n\nКакая услуга нужна? Можно выбрать несколько. "
                          "Если не уверены — нажмите <b>Продолжить</b>, определим на бесплатном осмотре."),
        "svc_all": ("Что нужно? Можно выбрать несколько. "
                    "Если не уверены — нажмите <b>Продолжить</b>, определим на осмотре."),
        "car_dokon": ("Марка машины и размер дисков/шин?\n"
                      "(например: <i>Malibu 2, R17</i> или <i>Cobalt, 185/75 R14</i>)\n"
                      "Если не знаете размер — напишите только марку, подберём сами."),
        "car_all": "Марка и год вашей машины? (например, Chevrolet Cobalt 2022)",
        "when": "Когда вам удобно приехать?",
        "when_other": "Какой день и время вам удобны? Напишите.",
        "ask_phone": "Отправьте номер телефона — нажмите кнопку ниже или напишите.",
        "ask_phone_hint": "\n\nВаш предыдущий номер: <b>{phone}</b> — можете написать его снова.",
        "phone_bad": "Введите номер правильно (например, +998 90 123 45 67) или нажмите кнопку.",
        "almost": "Почти готово ✅",
        "sum_title": "Проверьте:",
        "sum_sent": "Заявка отправлена ✅",
        "tbd": "определим на осмотре",
        "prices_title": "Цены",
        "prices_footer": ("\n\nТочная цена зависит от типа машины. Цена фиксируется письменно и потом не растёт. "
                          "Если взять несколько услуг вместе — дешевле."),
        "promo_none": ("Пока акций нет. Не отключайте бота — о новых акциях "
                       "сообщим здесь первыми 🔔"),
        "addr": "📍 <b>Адрес:</b> {addr}\n🕘 <b>Время работы:</b> {hours}\n📞 {phone}",
        "map_btn": "🗺 Открыть на карте",
        "contact": "📞 Позвоните: <b>{phone}</b>",
        "contact_admin_btn": "✍️ Написать администратору",
        "my_none": "Пока записей нет.",
        "my_title": "<b>Ваши последние записи</b>",
        "my_row_fallback": "осмотр",
        "ref": ("🎁 <b>Пригласите друга</b>\n\nОтправьте эту ссылку другу. "
                "Когда он придёт по ней и получит первую услугу, <b>вам обоим</b>: {bonus}\n"
                "Приведёте {tier_n} друзей — {tier}.\n\n"
                "{link}\n\nВы пригласили: <b>{n}</b>\nВоспользовались услугой: <b>{done} / {tier_n}</b>"),
        "ref_friend_msg": ("🎁 Спасибо за первую услугу. Вам тоже: <b>{bonus}</b>\n"
                           "Покажите это сообщение при визите."),
        "ref_tier_msg": ("🏆 {n} ваших друзей воспользовались нашими услугами. Подарок: <b>{tier}</b>\n"
                         "Покажите это сообщение при визите."),
        "i_ref": "🎁 Пригласить друга",
        "ref_nolink": "(имя бота не определено)",
        "feedback_thanks": "Спасибо, мы передали ваш отзыв руководству. Скоро свяжемся с вами.",
        "done_msg": ("✅ Ваша машина готова! Спасибо, что выбрали Automaximus.\n\n"
                     "Как вы оцениваете наш сервис?"),
        "ref_bonus_msg": ("🎉 Приглашённый вами друг воспользовался нашими услугами!\n"
                          "Вам: <b>{bonus}</b>. Покажите это сообщение при визите."),
        "rated_already": "Ваша оценка уже принята.",
        "rated_good": ("Спасибо! 🙌 Если не сложно, оставьте короткий отзыв — "
                       "это поможет другим водителям с выбором."),
        "rated_bad": ("Простите, что не оправдали ожиданий. Напишите, что не понравилось — "
                      "обязательно исправим."),
        "review_btn": "✍️ Оставить отзыв",
        "thanks_short": "Спасибо!",
        "photo_from_work": "📸 Из процесса работы (заявка #{id}):",
        "reminder_default": "С момента услуги «{service}» прошло много времени.",
        "abandoned": "Вы не завершили запись 🙂 Продолжим? Осталась всего минута.",
        "b_book": "🗓 Записаться",
        "b_shop": "🛞 Диски и шины",
        "b_detail": "✨ Детейлинг",
        "b_promo": "🔥 Акции",
        "b_prices": "💰 Цены",
        "b_addr": "📍 Адрес и время работы",
        "b_my": "📋 Мои записи",
        "b_ref": "🎁 Пригласить друга",
        "b_contact": "📞 Связаться",
        "b_phone": "📱 Отправить номер",
        "b_cancel": "↩️ Отмена",
        "b_lang": "🌐 O‘zbekcha",
        "i_next": "Продолжить ➡️",
        "i_cancel": "Отмена",
        "i_skip": "Пропустить",
        "i_other_day": "Другой день — напишу",
        "i_confirm": "✅ Подтвердить",
        "i_confirm_cancel": "❌ Отмена",
        "i_resume": "▶️ Продолжить",
        "i_no_thanks": "Нет, спасибо",
    },
}

# Kunlar: callback ma'lumoti va bazadagi qiymat o'zbekcha qoladi, ekranda tilga qarab ko'rsatiladi
DAYS = {
    "Bugun": {"uz": "Bugun", "ru": "Сегодня"},
    "Ertaga": {"uz": "Ertaga", "ru": "Завтра"},
    "Shu hafta": {"uz": "Shu hafta", "ru": "На этой неделе"},
}

STATUS = {
    "uz": {"new": "🆕 Yangi", "called": "📞 Bog‘lanildi", "done": "✅ Ish tugadi", "cancelled": "❌ Bekor qilindi"},
    "ru": {"new": "🆕 Новая", "called": "📞 Связались", "done": "✅ Работа выполнена", "cancelled": "❌ Отменена"},
}

GROUP_NAMES = {"dokon": {"uz": "Do‘kon", "ru": "Магазин"}, "detailing": {"uz": "Detailing", "ru": "Детейлинг"}}


def norm_lang(value: str | None) -> str:
    return value if value in LANGS else DEFAULT_LANG


def tr(lang: str, key: str, **kw) -> str:
    text = T.get(lang, T[DEFAULT_LANG]).get(key) or T[DEFAULT_LANG][key]
    return text.format(**kw) if kw else text


def btn(lang: str, key: str) -> str:
    """Oddiy klaviatura tugmasi matni: btn('ru', 'shop')."""
    return tr(lang, "b_" + key)


_BTN_LOOKUP: dict[str, str] = {}
for _lang in LANGS:
    for _key in T[_lang]:
        if _key.startswith("b_"):
            _BTN_LOOKUP[T[_lang][_key]] = _key[2:]


def btn_key(text: str) -> str | None:
    """Kelgan matn qaysi tugma ekanini (qaysi tilda bo'lsa ham) aniqlaydi: '🛞 Диски и шины' -> 'shop'."""
    return _BTN_LOOKUP.get(text)


def day_label(value: str, lang: str) -> str:
    return DAYS.get(value, {}).get(lang, value)


def status_label(status: str, lang: str) -> str:
    return STATUS[norm_lang(lang)].get(status, status)
