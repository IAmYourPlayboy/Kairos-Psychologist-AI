/** @type {import('next').NextConfig} */

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8001";

const nextConfig = {
  reactStrictMode: true,

  // Проксируем /api/* запросы на FastAPI бекенд (порт 8001).
  // В продакшене это делает Nginx, локально — Next dev server.
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
