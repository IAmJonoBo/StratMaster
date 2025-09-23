/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
  },
  env: {
    STRATMASTER_API_URL: process.env.STRATMASTER_API_URL || 'http://localhost:8080',
  },
}

module.exports = nextConfig