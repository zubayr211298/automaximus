// bot/config.py bilan bir xil matnlar — ikkisini sinxron tutish uchun shu yerda bitta joyda.
export const GROUP_TITLES: Record<string, string> = {
  dokon: "🛞 Do'kon: disk, balon, aksessuar",
  detailing: "✨ Detailing xizmatlari",
};

export const DAY_OPTIONS = ["Bugun", "Ertaga", "Shu hafta"] as const;

export const BOT_API_URL =
  process.env.NEXT_PUBLIC_BOT_API_URL?.replace(/\/$/, "") || "http://localhost:8080";
