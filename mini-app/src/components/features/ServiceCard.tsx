"use client";

import type { Service } from "@/lib/api";

export function ServiceCard({
  service,
  selected,
  onToggle,
}: {
  service: Service;
  selected: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
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
        {selected ? "✅" : "▫️"} <strong>{service.name}</strong>
      </span>
      <span style={{ color: "var(--text-soft)", fontSize: 13 }}>{service.price}</span>
    </button>
  );
}
