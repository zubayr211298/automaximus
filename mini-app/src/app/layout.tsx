import type { ReactNode } from "react";
import Script from "next/script";
import { TelegramProvider } from "@/providers/TelegramProvider";
import "@/styles/globals.css";

export const metadata = {
  title: "Automaximus — yozilish",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="uz">
      <head>
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
      </head>
      <body>
        <TelegramProvider>{children}</TelegramProvider>
      </body>
    </html>
  );
}
