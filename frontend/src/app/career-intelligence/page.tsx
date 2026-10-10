'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function CareerIntelligenceRedirectPage() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/resume-builder')
  }, [router])

  return (
    <div className="min-h-screen bg-[#070814] flex items-center justify-center">
      <div className="flex items-center gap-3 text-cyan-400 font-mono text-sm">
        <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
        <span>Redirecting to AI Career Intelligence &amp; Resume Studio...</span>
      </div>
    </div>
  )
}
