import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const backendBaseUrl =
      process.env.BACKEND_API_BASE_URL ?? "http://127.0.0.1:8001";

    return [
      {
        source: "/api/:path*",
        destination: `${backendBaseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
