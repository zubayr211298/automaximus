"use client";

import { cx } from "@/lib/utils";

export function Chip({
  label,
  selected,
  onClick,
}: {
  label: string;
  selected?: boolean;
  onClick?: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        display: "block",
        width: "100%",
        textAlign: "left",
        padding: "14px 16px",
        marginBottom: 8,
        borderRadius: "var(--radius)",
        border: `1px solid ${selected ? "var(--accent)" : "var(--card-2)"}`,
        background: selected ? "rgba(215,24,42,0.12)" : "var(--card)",
        color: "var(--text)",
      }}
      className={cx("chip", selected && "chip-selected")}
    >
      {selected ? "✅ " : "▫️ "}
      {label}
    </button>
  );
}
