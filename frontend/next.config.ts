import type { NextConfig } from 'next'

const config: NextConfig = {
  reactStrictMode: true,
  experimental: {
    serverActions: { allowedOrigins: ['localhost:3000'] },
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        ],
      },
    ]
  },
  async redirects() {
    return [
      {
        source: '/company-interview',
        destination: '/company-mode',
        permanent: false,
      },
      {
        source: '/salary-negotiation',
        destination: '/negotiation',
        permanent: false,
      },
      {
        source: '/career-intelligence',
        destination: '/resume-builder',
        permanent: false,
      },
      {
        source: '/roadmap',
        destination: '/learning',
        permanent: false,
      },
      {
        source: '/reports/:sessionId',
        destination: '/report/:sessionId',
        permanent: false,
      },
      {
        source: '/reports',
        destination: '/dashboard',
        permanent: false,
      },
    ]
  },
}

export default config
