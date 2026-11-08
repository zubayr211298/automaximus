"use client";

import { useState } from "react";
import { useBookingStore } from "@/store/bookingStore";
import { submitLead } from "@/lib/api";
import { useTelegramContext } from "@/providers/TelegramProvider";
import { useT } from "@/hooks/useT";

export function useBooking() {
  const state = useBookingStore();
  const { user, initData } = useTelegramContext();
  const { t } = useT();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirm() {
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitLead({
        name: user?.first_name || user?.username || "Telegram foydalanuvchi",
        phone: state.phone,
        car: state.car,
        services: state.services,
        day: state.day,
        source: "miniapp",
        channel: "miniapp",
        initData,
      });
      if (!res.ok) {
        setError(res.error || t("errGeneric"));
        return false;
      }
      state.reset();
      return true;
    } catch {
      setError(t("errNetwork"));
      return false;
    } finally {
      setSubmitting(false);
    }
  }

  return { ...state, submitting, error, confirm };
}
