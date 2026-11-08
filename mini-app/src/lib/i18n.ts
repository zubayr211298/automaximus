export type Lang = "uz" | "ru";

export const LANGS: Lang[] = ["uz", "ru"];

export const UI = {
  uz: {
    subtitle: "Xizmat tanlang, qolganini bitta daqiqada yakunlaymiz.",
    loading: "Yuklanmoqda...",
    empty: "Ro'yxat bo'sh. Bilmasangiz ham davom etishingiz mumkin.",
    next: "Davom etish ➡️",
    groupDokon: "🛞 Do'kon: disk, balon, aksessuar",
    groupDetailing: "✨ Detailing xizmatlari",
    back: "← Orqaga",
    carQ: "Mashinangiz rusumi va yili?",
    carPh: "masalan, Chevrolet Cobalt 2022",
    dayQ: "Qachon kelishingiz qulay?",
    dayToday: "Bugun",
    dayTomorrow: "Ertaga",
    dayWeek: "Shu hafta",
    phoneQ: "Telefon raqamingiz?",
    phoneErr: "Raqamni to'g'ri kiriting (masalan, +998 90 123 45 67).",
    checkTitle: "Tekshiring",
    toBeDetermined: "ko'rikda aniqlanadi",
    confirm: "✅ Tasdiqlash",
    sending: "Yuborilmoqda...",
    errGeneric: "Xatolik yuz berdi, qayta urinib ko'ring.",
    errNetwork: "Tarmoq xatosi. Internetni tekshirib qayta urinib ko'ring.",
    thanksTitle: "Rahmat! So'rovingiz qabul qilindi.",
    thanksText: "Tez orada qo'ng'iroq qilib, aniq narxni aytamiz.",
    close: "Yopish",
    langLabel: "Til / Язык",
  },
  ru: {
    subtitle: "Выберите услугу — остальное оформим за минуту.",
    loading: "Загрузка...",
    empty: "Список пуст. Можно продолжить и без выбора.",
    next: "Продолжить ➡️",
    groupDokon: "🛞 Магазин: диски, шины, аксессуары",
    groupDetailing: "✨ Услуги детейлинга",
    back: "← Назад",
    carQ: "Марка и год вашей машины?",
    carPh: "например, Chevrolet Cobalt 2022",
    dayQ: "Когда вам удобно приехать?",
    dayToday: "Сегодня",
    dayTomorrow: "Завтра",
    dayWeek: "На этой неделе",
    phoneQ: "Ваш номер телефона?",
    phoneErr: "Введите номер правильно (например, +998 90 123 45 67).",
    checkTitle: "Проверьте",
    toBeDetermined: "определим на осмотре",
    confirm: "✅ Подтвердить",
    sending: "Отправка...",
    errGeneric: "Произошла ошибка, попробуйте ещё раз.",
    errNetwork: "Ошибка сети. Проверьте интернет и попробуйте ещё раз.",
    thanksTitle: "Спасибо! Ваша заявка принята.",
    thanksText: "Скоро позвоним и назовём точную цену.",
    close: "Закрыть",
    langLabel: "Til / Язык",
  },
} as const;

export type UiKey = keyof (typeof UI)["uz"];

type Localized = { name: string; price: string; name_ru?: string; price_ru?: string };

export function serviceName(s: Pick<Localized, "name" | "name_ru">, lang: Lang): string {
  return lang === "ru" && s.name_ru ? s.name_ru : s.name;
}

export function servicePrice(s: Pick<Localized, "price" | "price_ru">, lang: Lang): string {
  return lang === "ru" && s.price_ru ? s.price_ru : s.price;
}

export function isLang(v: unknown): v is Lang {
  return v === "uz" || v === "ru";
}
