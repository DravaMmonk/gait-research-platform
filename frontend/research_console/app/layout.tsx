import "./globals.css";
import { ReactNode } from "react";

export const metadata = {
  title: "Hound Forward Research Console",
  description: "Research UI scaffold for the Azure AI-native canine movement platform.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
