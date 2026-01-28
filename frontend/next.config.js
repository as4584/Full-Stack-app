/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  reactStrictMode: true,
  poweredByHeader: false,
  
  // Optimize for production
  compress: true,
  
  // Image optimization
  images: {
    domains: ['api.lexmakesit.com'],
    formats: ['image/webp'],
  },
  
  // Reduce build time by excluding non-essential directories
  typescript: {
    ignoreBuildErrors: false,
  },
  
  eslint: {
    ignoreDuringBuilds: false,
  },
}

module.exports = nextConfig
