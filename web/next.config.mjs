/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  async rewrites() {
    if (process.env.NODE_ENV === "production") return [];

    const target =
      process.env.LOCAL_API_PROXY_TARGET ??
      "http://127.0.0.1:8010/api/v1";
    return [
      {
        source: "/api/local-backend/:path*",
        destination: `${target.replace(/\/+$/, "")}/:path*`,
      },
    ];
  },
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "X-Frame-Options", value: "DENY" },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
    ] }];
  },
};
export default nextConfig;
