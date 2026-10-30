import { BOT_API_URL } from "./constants";

export type Service = {
  name: string;
  group: "dokon" | "detailing";
  price: string;
};

export type ServicesResponse = {
  services: Service[];
  groupTitles: Record<string, string>;
};

export async function fetchServices(): Promise<ServicesResponse> {
  const res = await fetch(`${BOT_API_URL}/services`);
  if (!res.ok) throw new Error(`/services ${res.status}`);
  return res.json();
}

export type LeadPayload = {
  name: string;
  phone: string;
  car: string;
  services: string[];
  day: string;
  source: string;
  channel: "miniapp";
  initData: string; // Telegram.WebApp.initData — bot tomonida HMAC bilan tekshiriladi
};

export type LeadResult = { ok: boolean; id?: number; error?: string };

export async function submitLead(payload: LeadPayload): Promise<LeadResult> {
  const res = await fetch(`${BOT_API_URL}/lead`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}
