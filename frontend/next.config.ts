import type { NextConfig } from "next";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {};

export default withSentryConfig(nextConfig, {
  // Sentry org/project — set these in environment or here
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  // Suppress source map upload logs during build
  silent: !process.env.CI,
  // Automatically tree-shake Sentry logger statements in production
  disableLogger: true,
  // Upload source maps to Sentry during build (requires SENTRY_AUTH_TOKEN env var)
  sourcemaps: {
    deleteSourcemapsAfterUpload: true,
  },
});
