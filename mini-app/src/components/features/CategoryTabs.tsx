"use client";

import { useT } from "@/hooks/useT";

export function CategoryTabs({
  active,
  onChange,
}: {
  active: "dokon" | "detailing";
  onChange: (group: "dokon" | "detailing") => void;
}) {
  const { t } = useT();
  const labels = { dokon: t("groupDokon"), detailing: t("groupDetailing") };

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
          {labels[group]}
        </button>
      ))}
    </div>
  );
}
