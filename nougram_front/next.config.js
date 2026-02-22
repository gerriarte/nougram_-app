/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  turbopack: {
    root: process.cwd(),
  },
};

module.exports = nextConfig;
