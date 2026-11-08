import type { ReactNode } from "react";
import Script from "next/script";
import { TelegramProvider } from "@/providers/TelegramProvider";
import { Header } from "@/components/layout/Header";
import "@/styles/globals.css";

export const metadata = {
  title: "Automaximus",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uz">
      <head>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      </head>
      <body>
        <TelegramProvider>
          <Header />
          {children}
        </TelegramProvider>
      </body>
    </html>
  );
}
