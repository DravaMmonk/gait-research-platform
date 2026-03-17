import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";

export const metadata = {
  title: "Hound Forward Agent Console",
  description: "Single-surface chat-first console for Hound Forward agent interactions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
