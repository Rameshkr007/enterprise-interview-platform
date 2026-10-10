'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function CompanyInterviewRedirectPage() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/company-mode')
  }, [router])

  return (
    <div className="min-h-screen bg-[#070814] flex items-center justify-center">
      <div className="flex items-center gap-3 text-amber-400 font-mono text-sm">
        <span className="w-3 h-3 rounded-full bg-amber-400 animate-ping" />
        <span>Redirecting to Company Calibration Simulation...</span>
      </div>
    </div>
  )
}
