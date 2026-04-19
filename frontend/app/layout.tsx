import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CARE — Customer Autonomous Resolution Engine",
  description:
    "An intelligent assistant that analyzes your request and makes the best decision for you. Fast, transparent, human-first customer support.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased">
        {/* Hero background image with living animations */}
        <div className="hero-bg" aria-hidden="true">
          <div className="hero-bg-image" />
          <div className="hero-bg-glow" />
          <div className="hero-bg-scanline" />
          <div className="hero-bg-vignette" />
        </div>
        <div className="ambient-bg" />
        <div className="relative z-10">{children}</div>
      </body>
    </html>
  );
}
