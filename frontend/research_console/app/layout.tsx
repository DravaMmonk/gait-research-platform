import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import { ReactNode } from "react";
import { Roboto } from "next/font/google";

const roboto = Roboto({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  display: "swap",
});

export const metadata = {
  title: "Hound Forward Agent Console",
  description: "Single-surface chat-first console for Hound Forward agent interactions.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className={roboto.className} suppressHydrationWarning>
        {children}
      </body>
    </html>
  );
}
