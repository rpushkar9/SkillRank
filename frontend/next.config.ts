import type { NextConfig } from "next";
import path from "path";
import { fileURLToPath } from "url";

// Pin the Turbopack workspace root to this app directory. Without this, Next may
// infer a parent directory as the root (e.g. when a stray lockfile exists higher
// up) and try to traverse folders it cannot read.
const appDir = path.dirname(fileURLToPath(import.meta.url));

const nextConfig: NextConfig = {
  turbopack: {
    root: appDir,
  },
};

export default nextConfig;
