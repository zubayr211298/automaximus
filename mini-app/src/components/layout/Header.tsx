"use client";

import { LangSwitch } from "./LangSwitch";

export function Header() {
  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        maxWidth: 480,
        margin: "0 auto",
        padding: "12px 16px 0",
      }}
    >
      <span style={{ fontWeight: 800, letterSpacing: ".08em", fontSize: 15 }}>AUTOMAXIMUS</span>
      <LangSwitch />
    </header>
  );
}
