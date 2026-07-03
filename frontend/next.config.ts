import type { NextConfig } from "next";
import path from "path";
import { config as dotenvConfig } from "dotenv";

// Load from root .env (one level up from frontend/)
dotenvConfig({ path: path.resolve(__dirname, "../.env") });

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;
