'use client'

import React, { Suspense, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

function InterviewRedirect() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get('sessionId')

  useEffect(() => {
    if (sessionId) {
      router.replace(`/interview/${sessionId}`)
    } else {
      router.replace('/interview/new')
    }
  }, [router, sessionId])

  return (
    <div className="min-h-screen bg-[#070814] flex items-center justify-center">
      <div className="flex items-center gap-3 text-cyan-400 font-mono text-sm">
        <span className="w-3 h-3 rounded-full bg-cyan-400 animate-ping" />
        <span>Initializing AI Interview Environment...</span>
      </div>
    </div>
  )
}

export default function InterviewIndexPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-[#070814] flex items-center justify-center text-cyan-400 font-mono text-sm">
          Loading Interview...
        </div>
      }
    >
      <InterviewRedirect />
    </Suspense>
  )
}
