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
  return (
    <div style={{ background: "var(--card)", borderRadius: "var(--radius)", padding: 16 }}>
      <h3 style={{ marginBottom: 12 }}>Tekshiring</h3>
      <p>🛠 {services.join(", ") || "ko'rikda aniqlanadi"}</p>
      <p>🚗 {car || "—"}</p>
      <p>🗓 {day || "—"}</p>
      <p>📱 {phone}</p>
    </div>
  );
}
