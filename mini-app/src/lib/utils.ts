export function normalizePhone(raw: string): string | null {
  let digits = raw.replace(/\D/g, "");
  if (digits.length === 9) digits = "998" + digits;
  if (digits.length < 9 || digits.length > 15) return null;
  return "+" + digits;
}

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}
