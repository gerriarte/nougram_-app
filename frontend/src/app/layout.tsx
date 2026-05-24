import type { Metadata } from "next";
import "./globals.css";
import { NougramCoreProvider } from '@/context/NougramCoreContext';
import { AdminProvider } from '@/context/AdminContext';
import { Toaster } from '@/components/ui/Toaster';
import { GoogleTagManager } from '@/components/analytics/GoogleTagManager';
import { RouteTrackerClient } from '@/components/analytics/RouteTrackerClient';
import { AuthSessionExpiredDialog } from '@/components/auth/AuthSessionExpiredDialog';

export const metadata: Metadata = {
  title: "Nougram Cotizador",
  description: "Calculadora de costos y cotizaciones",
  icons: {
    icon: [{ url: "/brand/Logo-iso-orange.svg", type: "image/svg+xml" }],
    shortcut: ["/brand/Logo-iso-orange.svg"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="font-sans antialiased bg-background text-slate-900" suppressHydrationWarning>
        <GoogleTagManager />
        <NougramCoreProvider>
          <AdminProvider>
            <RouteTrackerClient />
            {children}
            <AuthSessionExpiredDialog />
            <Toaster />
          </AdminProvider>
        </NougramCoreProvider>
      </body>
    </html>
  );
}
