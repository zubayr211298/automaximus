"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { CategoryTabs } from "@/components/features/CategoryTabs";
import { ServiceCard } from "@/components/features/ServiceCard";
import { fetchServices, type Service } from "@/lib/api";
import { useBookingStore } from "@/store/bookingStore";

export default function Home() {
  const router = useRouter();
  const [group, setGroup] = useState<"dokon" | "detailing">("detailing");
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const { services: selected, toggleService, start, goTo } = useBookingStore();

  useEffect(() => {
    fetchServices()
      .then((r) => setServices(r.services))
      .catch(() => setServices([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    start(group);
  }, [group, start]);

  const visible = services.filter((s) => s.group === group);

  return (
    <main className="screen">
      <h1 style={{ fontSize: 22, marginBottom: 4 }}>Automaximus</h1>
      <p style={{ color: "var(--text-soft)", marginBottom: 16 }}>
        Xizmat tanlang, qolganini bitta daqiqada yakunlaymiz.
      </p>

      <CategoryTabs active={group} onChange={setGroup} />

      {loading && <p style={{ color: "var(--text-soft)" }}>Yuklanmoqda...</p>}
      {!loading && visible.length === 0 && (
        <p style={{ color: "var(--text-soft)" }}>Ro'yxat bo'sh. Bilmasangiz ham davom etishingiz mumkin.</p>
      )}

      {visible.map((s) => (
        <ServiceCard
          key={s.name}
          service={s}
          selected={selected.includes(s.name)}
          onToggle={() => toggleService(s.name)}
        />
      ))}

      <button
        onClick={() => {
          goTo("car");
          router.push("/booking");
        }}
        style={{
          position: "fixed",
          left: 16,
          right: 16,
          bottom: 16,
          maxWidth: 448,
          margin: "0 auto",
          padding: "14px",
          borderRadius: 999,
          background: "var(--accent)",
          color: "#fff",
          fontWeight: 700,
          border: "none",
        }}
      >
        Davom etish ➡️
      </button>
    </main>
  );
}
