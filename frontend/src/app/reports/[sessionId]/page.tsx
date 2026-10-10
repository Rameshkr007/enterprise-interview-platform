'use client'

import { useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'

export default function ReportsRedirectPage() {
  const router = useRouter()
  const params = useParams()
  const sessionId = params?.sessionId

  useEffect(() => {
    if (sessionId) {
      router.replace(`/report/${sessionId}`)
    } else {
      router.replace('/dashboard')
    }
  }, [router, sessionId])

  return (
    <div className="min-h-screen bg-[#070814] flex items-center justify-center">
      <div className="flex items-center gap-3 text-cyan-400 font-mono text-sm">
        <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
        <span>Loading Interview Debrief Report...</span>
      </div>
    </div>
  )
}
