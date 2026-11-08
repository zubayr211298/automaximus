import { create } from "zustand";
import type { Service } from "@/lib/api";

// bot.py BOOKING_STATES bilan bir xil bosqichlar: svc -> car -> day -> phone -> confirm
export type BookingStep = "svc" | "car" | "day" | "phone" | "confirm";

export type BookingState = {
  group: "dokon" | "detailing" | null;
  step: BookingStep;
  services: string[];
  car: string;
  day: string;
  phone: string;
};

type BookingActions = {
  catalog: Service[];
  setCatalog: (catalog: Service[]) => void;
  start: (group: "dokon" | "detailing" | null) => void;
  toggleService: (name: string) => void;
  setCar: (car: string) => void;
  setDay: (day: string) => void;
  setPhone: (phone: string) => void;
  goTo: (step: BookingStep) => void;
  reset: () => void;
};

const initial: BookingState = {
  group: null,
  step: "svc",
  services: [],
  car: "",
  day: "",
  phone: "",
};

export const useBookingStore = create<BookingState & BookingActions>((set) => ({
  ...initial,
  catalog: [],
  setCatalog: (catalog) => set({ catalog }),
  start: (group) => set({ ...initial, group, step: "svc" }),
  toggleService: (name) =>
    set((s) => ({
      services: s.services.includes(name)
        ? s.services.filter((x) => x !== name)
        : [...s.services, name],
    })),
  setCar: (car) => set({ car, step: "day" }),
  setDay: (day) => set({ day, step: "phone" }),
  setPhone: (phone) => set({ phone, step: "confirm" }),
  goTo: (step) => set({ step }),
  reset: () => set(initial),
}));
