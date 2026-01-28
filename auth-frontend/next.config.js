/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    reactStrictMode: true,
    // No rewrites, no redirects - this is a pure auth app
    // All auth logic happens via API calls to the backend
};

module.exports = nextConfig;
