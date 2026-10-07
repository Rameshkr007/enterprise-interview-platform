'use client'

import React, { useEffect, useState } from 'react'

interface CoachWhisperProps {
  silenceSeconds: number
  fillerCount: number
  isSpeaking: boolean
}

export function CoachWhisper({ silenceSeconds, fillerCount, isSpeaking }: CoachWhisperProps) {
  const [hint, setHint] = useState<string | null>(null)
  const [visible, setVisible] = useState<boolean>(false)

  useEffect(() => {
    let activeHint: string | null = null

    if (silenceSeconds > 4 && isSpeaking) {
      activeHint = '💡 Silence detected — Take a breath, state your core idea, or structure using Situation → Action → Result.'
    } else if (fillerCount > 5) {
      activeHint = '🎯 Filler words detected — It is okay to pause in silence for a second rather than saying "um" or "like".'
    }

    if (activeHint) {
      setHint(activeHint)
      setVisible(true)
    } else {
      const timeout = setTimeout(() => {
        setVisible(false)
      }, 3000)
      return () => clearTimeout(timeout)
    }
  }, [silenceSeconds, fillerCount, isSpeaking])

  if (!visible || !hint) return null

  return (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-50 animate-slide-down max-w-md w-full px-4 pointer-events-none">
      <div className="flex items-center gap-3 px-4 py-2.5 rounded-xl bg-slate-900/90 border border-amber-400/40 shadow-2xl backdrop-blur-md text-amber-200 text-xs">
        <span className="text-base animate-pulse">🤫</span>
        <div className="flex-1 font-medium">{hint}</div>
      </div>
    </div>
  )
}
