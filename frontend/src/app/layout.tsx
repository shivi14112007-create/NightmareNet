import type { Metadata, Viewport } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import { ThemeProvider } from "@/lib/theme";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800", "900"],
  display: "swap",
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#030712",
};

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "https://frontend-aj5.vercel.app"
  ),

  title: "NightmareNet — Autonomous AI Self-Improvement Platform",

  description:
    "Force neural networks to learn invariant structures through Dream & Nightmare cycles. Autonomous training, adversarial stress-testing, and knowledge compression.",

  keywords: [
    "AI",
    "machine learning",
    "neural networks",
    "adversarial training",
    "model compression",
    "dream",
    "nightmare",
    "robustness",
  ],

  authors: [{ name: "Adit Jain" }],

  openGraph: {
    title: "NightmareNet — Autonomous AI Self-Improvement",
    description:
      "Dream & Nightmare cycles that force models to learn what matters.",
    url: "/",
    siteName: "NightmareNet",
    locale: "en_US",
    type: "website",
  },

  twitter: {
    card: "summary_large_image",
    title: "NightmareNet — Autonomous AI Self-Improvement",
    description:
      "Dream & Nightmare cycles that force models to learn what matters.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${jetbrainsMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="scanlines min-h-full flex flex-col bg-void text-text font-sans" suppressHydrationWarning>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){try{var t=localStorage.getItem('nightmarenet-theme');var d=document.documentElement;if(t==='light'){d.classList.add('light')}else{d.classList.add('dark')}}catch(e){document.documentElement.classList.add('dark')}})()`,
          }}
        />
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
