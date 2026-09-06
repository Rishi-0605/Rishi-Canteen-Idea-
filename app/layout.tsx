import type { Metadata, Viewport } from "next";
import "./globals.css";
import SplashGate from "@/components/splash/SplashGate";
import Navbar from "@/components/layout/Navbar";
import Footer from "@/components/layout/Footer";
import BottomNav from "@/components/layout/BottomNav";
import LocationModal from "@/components/layout/LocationModal";
import CartDrawer from "@/components/cart/CartDrawer";
import ToastHost from "@/components/ui/ToastHost";

export const metadata: Metadata = {
  metadataBase: new URL("https://techrush.example.com"),
  title: "TECHRUSH — Technology. Delivered Faster.",
  description:
    "Shop smartphones, laptops, TVs, appliances and more with fast local delivery from TECHRUSH. Estimated delivery in as little as 30 minutes from nearby retail partners.",
  icons: {
    icon: [{ url: "/favicon.svg", type: "image/svg+xml" }],
  },
  openGraph: {
    title: "TECHRUSH — Technology. Delivered Faster.",
    description: "Quick commerce for electronics. Need tech? Get it fast.",
    siteName: "TECHRUSH",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "TECHRUSH — Technology. Delivered Faster.",
    description: "Quick commerce for electronics. Need tech? Get it fast.",
  },
};

export const viewport: Viewport = {
  themeColor: "#04060d",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-navy-radial bg-fixed font-sans antialiased">
        <SplashGate>
          <a
            href="#main-content"
            className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[200] focus:rounded-lg focus:bg-rush focus:px-4 focus:py-2 focus:text-white"
          >
            Skip to content
          </a>
          <Navbar />
          <main id="main-content" className="pb-16 md:pb-0">
            {children}
          </main>
          <Footer />
          <BottomNav />
          <LocationModal />
          <CartDrawer />
          <ToastHost />
        </SplashGate>
      </body>
    </html>
  );
}
