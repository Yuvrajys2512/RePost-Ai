import type { Metadata } from "next";
import "./globals.css";
import { AnalyticsProvider } from "./providers";

export const metadata: Metadata = {
  title: "RePost AI",
  description: "Repurpose YouTube videos into platform-native content.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AnalyticsProvider>{children}</AnalyticsProvider>
      </body>
    </html>
  );
}

