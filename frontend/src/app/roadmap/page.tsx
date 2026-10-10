'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function RoadmapRedirectPage() {
  const router = useRouter()
  useEffect(() => {
    router.replace('/learning')
  }, [router])

  return (
    <div className="min-h-screen bg-[#070814] flex items-center justify-center">
      <div className="flex items-center gap-3 text-violet-400 font-mono text-sm">
        <span className="w-3 h-3 rounded-full bg-violet-400 animate-ping" />
        <span>Redirecting to Personalized Learning Roadmap...</span>
      </div>
    </div>
  )
}
