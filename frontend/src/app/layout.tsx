import type { Metadata } from 'next'
import './globals.css'
import { QueryProvider } from '@/components/providers/QueryProvider'

export const metadata: Metadata = {
  title: 'InterviewAI — Enterprise Mock Interview & ATS Analyzer',
  description:
    'AI-powered mock interview platform with semantic ATS resume analysis, LangGraph adaptive questioning, and real-time audio analytics.',
  keywords: 'mock interview, ATS analyzer, AI interview, resume scoring, job preparation',
  openGraph: {
    title: 'InterviewAI — Enterprise Mock Interview Platform',
    description: 'Ace your next interview with AI-powered coaching.',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
      </head>
      <body className="w-full max-w-full overflow-x-hidden">
        <QueryProvider>
          <main className="relative z-10 min-h-screen w-full max-w-full overflow-x-hidden">{children}</main>
        </QueryProvider>
      </body>
    </html>
  )
}
