"use client";

import { useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { Chip } from "@/components/ui/Chip";
import { BookingSummary } from "@/components/features/BookingSummary";
import { DAY_OPTIONS } from "@/lib/constants";
import { normalizePhone } from "@/lib/utils";
import { useBooking } from "@/hooks/useBooking";

// Bosqichlar bot.py BOOKING_STATES bilan bir xil: car -> day -> phone -> confirm
// (svc bosqichi bosh sahifada, "page.tsx"da bajariladi)
export default function BookingPage() {
  const router = useRouter();
  const booking = useBooking();
  const [carInput, setCarInput] = useState(booking.car);
  const [phoneInput, setPhoneInput] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);

  async function handleConfirm() {
    const ok = await booking.confirm();
    if (ok) router.push("/");
  }

  return (
    <main className="screen">
      <button
        onClick={() => (booking.step === "car" ? router.push("/") : booking.goTo(prevStep(booking.step)))}
        style={{ background: "none", border: "none", color: "var(--text-soft)", marginBottom: 16 }}
      >
        ← Orqaga
      </button>

      {booking.step === "car" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>Mashinangiz rusumi va yili?</h2>
          <input
            placeholder="masalan, Chevrolet Cobalt 2022"
            value={carInput}
            onChange={(e) => setCarInput(e.target.value)}
            style={{
              width: "100%",
              padding: 14,
              borderRadius: "var(--radius)",
              background: "var(--card)",
              border: "1px solid var(--card-2)",
              color: "var(--text)",
            }}
          />
          <button onClick={() => booking.setCar(carInput)} style={primaryButtonStyle}>
            Davom etish ➡️
          </button>
        </section>
      )}

      {booking.step === "day" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>Qachon kelishingiz qulay?</h2>
          {DAY_OPTIONS.map((day) => (
            <Chip key={day} label={day} selected={booking.day === day} onClick={() => booking.setDay(day)} />
          ))}
        </section>
      )}

      {booking.step === "phone" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>Telefon raqamingiz?</h2>
          <input
            placeholder="+998 90 123 45 67"
            value={phoneInput}
            onChange={(e) => setPhoneInput(e.target.value)}
            style={{
              width: "100%",
              padding: 14,
              borderRadius: "var(--radius)",
              background: "var(--card)",
              border: "1px solid var(--card-2)",
              color: "var(--text)",
            }}
          />
          {phoneError && <p style={{ color: "var(--accent-soft)", marginTop: 8 }}>{phoneError}</p>}
          <button
            onClick={() => {
              const normalized = normalizePhone(phoneInput);
              if (!normalized) {
                setPhoneError("Raqamni to'g'ri kiriting (masalan, +998 90 123 45 67).");
                return;
              }
              booking.setPhone(normalized);
            }}
            style={primaryButtonStyle}
          >
            Davom etish ➡️
          </button>
        </section>
      )}

      {booking.step === "confirm" && (
        <section>
          <BookingSummary services={booking.services} car={booking.car} day={booking.day} phone={booking.phone} />
          {booking.error && <p style={{ color: "var(--accent-soft)", marginTop: 12 }}>{booking.error}</p>}
          <button onClick={handleConfirm} disabled={booking.submitting} style={{ ...primaryButtonStyle, marginTop: 16 }}>
            {booking.submitting ? "Yuborilmoqda..." : "✅ Tasdiqlash"}
          </button>
        </section>
      )}
    </main>
  );
}

function prevStep(step: "svc" | "car" | "day" | "phone" | "confirm") {
  const order = ["car", "day", "phone", "confirm"] as const;
  const idx = order.indexOf(step as (typeof order)[number]);
  return idx <= 0 ? "car" : order[idx - 1];
}

const primaryButtonStyle: CSSProperties = {
  width: "100%",
  padding: 14,
  marginTop: 12,
  borderRadius: 999,
  background: "var(--accent)",
  color: "#fff",
  fontWeight: 700,
  border: "none",
};
