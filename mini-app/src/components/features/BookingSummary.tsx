"use client";

import { useT } from "@/hooks/useT";

// bot.py summary_text() bilan bir xil "Tekshiring" ekrani
export function BookingSummary({
  services,
  car,
  day,
  phone,
}: {
  services: string[];
  car: string;
  day: string;
  phone: string;
}) {
  const { t } = useT();

  return (
    <div style={{ background: "var(--card)", borderRadius: "var(--radius)", padding: 16 }}>
      <h3 style={{ marginBottom: 12 }}>{t("checkTitle")}</h3>
      <p>🛠 {services.join(", ") || t("toBeDetermined")}</p>
      <p>🚗 {car || "—"}</p>
      <p>🗓 {day || "—"}</p>
      <p>📱 {phone}</p>
    </div>
  );
}
