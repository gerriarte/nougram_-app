/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  // Force Next.js to treat frontend/ as the tracing root in monorepo-like deploys.
  outputFileTracingRoot: process.cwd(),
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
  compress: true,
  poweredByHeader: false,
  experimental: {
    optimizePackageImports: ["recharts", "lucide-react"],
  },
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  async headers() {
    const noStore = [{ key: "Cache-Control", value: "no-store, must-revalidate" }];
    return [
      { source: "/", headers: noStore },
      { source: "/login", headers: noStore },
      { source: "/register", headers: noStore },
      { source: "/accept-invitation", headers: noStore },
    ];
  },
  turbopack: {
    root: process.cwd(),
  },
};

module.exports = nextConfig;
