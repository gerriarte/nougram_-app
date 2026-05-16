/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async redirects() {
    return [
      {
        source: "/projects/new",
        destination: "/dashboard/quotes/create",
        permanent: false,
      },
    ];
  },
  experimental: {
    optimizePackageImports: ["lucide-react"],
  },
  turbopack: {
    root: process.cwd(),
  },
};

module.exports = nextConfig;
