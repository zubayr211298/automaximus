"use client";

import { useState, type CSSProperties } from "react";
import { useRouter } from "next/navigation";
import { Chip } from "@/components/ui/Chip";
import { BookingSummary } from "@/components/features/BookingSummary";
import { DAY_OPTIONS } from "@/lib/constants";
import { serviceName } from "@/lib/i18n";
import { normalizePhone } from "@/lib/utils";
import { useBooking } from "@/hooks/useBooking";
import { useBookingStore } from "@/store/bookingStore";
import { useT } from "@/hooks/useT";
import { useTelegramContext } from "@/providers/TelegramProvider";

// Bosqichlar bot.py BOOKING_STATES bilan bir xil: car -> day -> phone -> confirm
// (svc bosqichi bosh sahifada, "page.tsx"da bajariladi)
export default function BookingPage() {
  const router = useRouter();
  const booking = useBooking();
  const catalog = useBookingStore((s) => s.catalog);
  const { t, lang } = useT();
  const { webApp } = useTelegramContext();
  const [carInput, setCarInput] = useState(booking.car);
  const [phoneInput, setPhoneInput] = useState("");
  const [phoneError, setPhoneError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function handleConfirm() {
    const ok = await booking.confirm();
    if (ok) setDone(true);
  }

  const localName = (name: string) => {
    const s = catalog.find((x) => x.name === name);
    return s ? serviceName(s, lang) : name;
  };
  const dayOption = DAY_OPTIONS.find((d) => d.value === booking.day);
  const dayLabel = dayOption ? t(dayOption.key) : booking.day;

  if (done) {
    return (
      <main className="screen">
        <section style={{ textAlign: "center", paddingTop: 48 }}>
          <div style={{ fontSize: 48 }}>✅</div>
          <h2 style={{ margin: "12px 0 8px" }}>{t("thanksTitle")}</h2>
          <p style={{ color: "var(--text-soft)" }}>{t("thanksText")}</p>
          <button
            onClick={() => {
              webApp?.close();
              router.push("/");
            }}
            style={{ ...primaryButtonStyle, marginTop: 24 }}
          >
            {t("close")}
          </button>
        </section>
      </main>
    );
  }

  return (
    <main className="screen">
      <button
        onClick={() => (booking.step === "car" ? router.push("/") : booking.goTo(prevStep(booking.step)))}
        style={{ background: "none", border: "none", color: "var(--text-soft)", marginBottom: 16 }}
      >
        {t("back")}
      </button>

      {booking.step === "car" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>{t("carQ")}</h2>
          <input
            placeholder={t("carPh")}
            value={carInput}
            onChange={(e) => setCarInput(e.target.value)}
            style={inputStyle}
          />
          <button onClick={() => booking.setCar(carInput)} style={primaryButtonStyle}>
            {t("next")}
          </button>
        </section>
      )}

      {booking.step === "day" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>{t("dayQ")}</h2>
          {DAY_OPTIONS.map((d) => (
            <Chip key={d.value} label={t(d.key)} selected={booking.day === d.value} onClick={() => booking.setDay(d.value)} />
          ))}
        </section>
      )}

      {booking.step === "phone" && (
        <section>
          <h2 style={{ marginBottom: 12 }}>{t("phoneQ")}</h2>
          <input
            placeholder="+998 90 123 45 67"
            value={phoneInput}
            onChange={(e) => setPhoneInput(e.target.value)}
            style={inputStyle}
          />
          {phoneError && <p style={{ color: "var(--accent-soft)", marginTop: 8 }}>{phoneError}</p>}
          <button
            onClick={() => {
              const normalized = normalizePhone(phoneInput);
              if (!normalized) {
                setPhoneError(t("phoneErr"));
                return;
              }
              setPhoneError(null);
              booking.setPhone(normalized);
            }}
            style={primaryButtonStyle}
          >
            {t("next")}
          </button>
        </section>
      )}

      {booking.step === "confirm" && (
        <section>
          <BookingSummary
            services={booking.services.map(localName)}
            car={booking.car}
            day={dayLabel}
            phone={booking.phone}
          />
          {booking.error && <p style={{ color: "var(--accent-soft)", marginTop: 12 }}>{booking.error}</p>}
          <button onClick={handleConfirm} disabled={booking.submitting} style={{ ...primaryButtonStyle, marginTop: 16 }}>
            {booking.submitting ? t("sending") : t("confirm")}
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

const inputStyle: CSSProperties = {
  width: "100%",
  padding: 14,
  borderRadius: "var(--radius)",
  background: "var(--card)",
  border: "1px solid var(--card-2)",
  color: "var(--text)",
};

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
