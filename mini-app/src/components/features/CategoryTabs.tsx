"use client";

import { GROUP_TITLES } from "@/lib/constants";

export function CategoryTabs({
  active,
  onChange,
}: {
  active: "dokon" | "detailing";
  onChange: (group: "dokon" | "detailing") => void;
}) {
  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
      {(["dokon", "detailing"] as const).map((group) => (
        <button
          key={group}
          onClick={() => onChange(group)}
          style={{
            flex: 1,
            padding: "10px 12px",
            borderRadius: 999,
            border: "1px solid var(--card-2)",
            background: active === group ? "var(--accent)" : "var(--card)",
            color: "var(--text)",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          {GROUP_TITLES[group]}
        </button>
      ))}
    </div>
  );
}
