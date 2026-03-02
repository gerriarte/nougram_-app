import type { Metadata } from "next";
import "./globals.css";
import { NougramCoreProvider } from '@/context/NougramCoreContext';
import { Toaster } from '@/components/ui/Toaster';

export const metadata: Metadata = {
  title: "Nougram Cotizador",
  description: "Calculadora de costos y cotizaciones",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <body className="font-sans antialiased bg-gray-50 text-slate-900" suppressHydrationWarning>

        <NougramCoreProvider>
          {children}
          <Toaster />
        </NougramCoreProvider>

      </body>
    </html>
  );
}
