import type { UiKey } from "./i18n";

// value — botga ketadigan (admin kartasida ko'rinadigan) o'zbekcha qiymat; ekranda key bo'yicha tarjima ko'rsatiladi
export const DAY_OPTIONS: { value: string; key: UiKey }[] = [
  { value: "Bugun", key: "dayToday" },
  { value: "Ertaga", key: "dayTomorrow" },
  { value: "Shu hafta", key: "dayWeek" },
];

export const BOT_API_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL?.replace(/\/$/, "") || "http://localhost:8080";
