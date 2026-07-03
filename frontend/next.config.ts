import type { NextConfig } from "next";
import path from "path";
import { config as dotenvConfig } from "dotenv";

// Load from root .env (one level up from frontend/)
dotenvConfig({ path: path.resolve(__dirname, "../.env") });

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/:path*",
      },
    ];
  },
};

export default nextConfig;
