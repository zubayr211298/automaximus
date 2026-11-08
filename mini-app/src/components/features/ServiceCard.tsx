"use client";

import type { Service } from "@/lib/api";
import { serviceName, servicePrice } from "@/lib/i18n";
import { useT } from "@/hooks/useT";

export function ServiceCard({
  service,
  selected,
  onToggle,
}: {
  service: Service;
  selected: boolean;
  onToggle: () => void;
}) {
  const { lang } = useT();

  return (
    <button
      type="button"
      onClick={onToggle}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        gap: 12,
        width: "100%",
        textAlign: "left",
        padding: "14px 16px",
        marginBottom: 8,
        borderRadius: "var(--radius)",
        border: `1px solid ${selected ? "var(--accent)" : "var(--card-2)"}`,
        background: selected ? "rgba(215,24,42,0.12)" : "var(--card)",
        color: "var(--text)",
      }}
    >
      <span>
        {selected ? "✅" : "▫️"} <strong>{serviceName(service, lang)}</strong>
      </span>
      <span style={{ color: "var(--text-soft)", fontSize: 13, textAlign: "right" }}>
        {servicePrice(service, lang)}
      </span>
    </button>
  );
}
