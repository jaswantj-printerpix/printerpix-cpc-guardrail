import type { Metadata } from "next";
import { Roboto } from "next/font/google";
import "./globals.css";

const roboto = Roboto({
  weight: ["400", "500", "700"],
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CPC Anomaly Alerts - Red Zone | Printerpix",
  description: "CPC anomaly detection and red zone monitoring",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${roboto.className} bg-white text-[#212121] min-h-screen antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
