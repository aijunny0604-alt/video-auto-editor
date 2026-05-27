/** @type {import('next').NextConfig} */
const isDemo = process.env.NEXT_PUBLIC_DEMO_MODE === "1";
const basePath = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

const nextConfig = isDemo
  ? {
      reactStrictMode: true,
      output: "export",
      images: { unoptimized: true },
      basePath,
      assetPrefix: basePath || undefined,
      trailingSlash: true,
    }
  : {
      reactStrictMode: true,
      async rewrites() {
        return [
          {
            source: "/api/:path*",
            destination: "http://localhost:8000/api/:path*",
          },
        ];
      },
    };

module.exports = nextConfig;
