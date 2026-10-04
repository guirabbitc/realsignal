import path from "node:path";
import { config } from "dotenv";
import type { NextConfig } from "next";

// One .env at the repo root serves every service.
config({ path: path.resolve(process.cwd(), "../../.env") });

const nextConfig: NextConfig = {};

export default nextConfig;
