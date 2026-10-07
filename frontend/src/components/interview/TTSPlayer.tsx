'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '@/lib/api'

interface TTSPlayerProps {
  text: string
  voice?: 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer'
  autoPlay?: boolean
  onStarted?: () => void
  onEnded?: () => void
}

type Status = 'idle' | 'loading' | 'playing' | 'paused' | 'error'

export function TTSPlayer({
  text,
  voice = 'nova',
  autoPlay = true,
  onStarted,
  onEnded,
}: TTSPlayerProps) {
  const [status, setStatus] = useState<Status>('idle')
  const [progress, setProgress] = useState(0)
  const [isBrowserVoice, setIsBrowserVoice] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null)

  // Browser Web Speech API fallback
  const speakWithBrowserTTS = useCallback(() => {
    if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
      setStatus('idle')
      return
    }

    try {
      window.speechSynthesis.cancel()

      const utterance = new SpeechSynthesisUtterance(text)
      utterance.rate = 1.05
      utterance.pitch = 1.0
      utteranceRef.current = utterance

      // Voice selection matching personality
      const voices = window.speechSynthesis.getVoices()
      const preferredVoice =
        voices.find(
          (v) =>
            v.lang.startsWith('en') &&
            (v.name.includes('Natural') ||
              v.name.includes('Google') ||
              v.name.includes('Jenny') ||
              v.name.includes('Aria') ||
              v.name.includes('Samantha') ||
              v.name.includes('Zira'))
        ) || voices.find((v) => v.lang.startsWith('en'))

      if (preferredVoice) {
        utterance.voice = preferredVoice
      }

      utterance.onstart = () => {
        setStatus('playing')
        setIsBrowserVoice(true)
        onStarted?.()

        // Estimate speech duration based on word count
        const words = text.split(/\s+/).length
        const estimatedMs = Math.max(2500, (words / 2.8) * 1000)
        const start = Date.now()

        if (intervalRef.current) clearInterval(intervalRef.current)
        intervalRef.current = setInterval(() => {
          const elapsed = Date.now() - start
          const pct = Math.min(99, (elapsed / estimatedMs) * 100)
          setProgress(pct)
        }, 150)
      }

      utterance.onend = () => {
        setStatus('idle')
        setProgress(100)
        if (intervalRef.current) clearInterval(intervalRef.current)
        onEnded?.()
      }

      utterance.onerror = () => {
        if (intervalRef.current) clearInterval(intervalRef.current)
        setStatus('idle')
      }

      window.speechSynthesis.speak(utterance)
    } catch {
      setStatus('idle')
    }
  }, [text, onStarted, onEnded])

  // Synthesize: Try backend OpenAI TTS first, fallback to browser Web Speech API
  const synthesize = useCallback(async () => {
    if (!text.trim()) return
    setStatus('loading')
    setProgress(0)
    setIsBrowserVoice(false)

    try {
      const res = await api.post<{
        audio_b64?: string
        format?: string
        use_browser_speech?: boolean
      }>('/resume-builder/tts/synthesize', { text, voice })

      if (res.data?.audio_b64 && !res.data.use_browser_speech) {
        // High fidelity OpenAI Opus audio
        const blob = new Blob(
          [Uint8Array.from(atob(res.data.audio_b64), (c) => c.charCodeAt(0))],
          { type: 'audio/ogg; codecs=opus' }
        )
        const url = URL.createObjectURL(blob)
        const audio = new Audio(url)
        audioRef.current = audio

        audio.onended = () => {
          setStatus('idle')
          setProgress(100)
          if (intervalRef.current) clearInterval(intervalRef.current)
          onEnded?.()
          URL.revokeObjectURL(url)
        }

        audio.onplay = () => {
          setStatus('playing')
          onStarted?.()
          intervalRef.current = setInterval(() => {
            if (audio.duration > 0) {
              setProgress((audio.currentTime / audio.duration) * 100)
            }
          }, 200)
        }

        audio.onerror = () => {
          speakWithBrowserTTS()
        }

        await audio.play()
      } else {
        // Explicit fallback requested by backend
        speakWithBrowserTTS()
      }
    } catch {
      // Backend unavailable or OpenAI API quota/key missing: seamless browser fallback
      speakWithBrowserTTS()
    }
  }, [text, voice, onStarted, onEnded, speakWithBrowserTTS])

  useEffect(() => {
    if (autoPlay && text) {
      synthesize()
    }
    return () => {
      audioRef.current?.pause()
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [text, autoPlay, synthesize])

  function togglePlay() {
    // If browser speech synthesis was used
    if (isBrowserVoice && typeof window !== 'undefined' && 'speechSynthesis' in window) {
      if (status === 'playing') {
        window.speechSynthesis.pause()
        setStatus('paused')
      } else if (status === 'paused') {
        window.speechSynthesis.resume()
        setStatus('playing')
      } else {
        speakWithBrowserTTS()
      }
      return
    }

    // If audio element was used
    if (!audioRef.current) {
      synthesize()
      return
    }

    if (status === 'playing') {
      audioRef.current.pause()
      setStatus('paused')
    } else {
      audioRef.current.play()
      setStatus('playing')
    }
  }

  return (
    <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-sm">
      {/* Control button */}
      <button
        onClick={togglePlay}
        disabled={status === 'loading'}
        className="w-9 h-9 rounded-full bg-indigo-500/20 hover:bg-indigo-500/30 flex items-center justify-center transition-all flex-shrink-0 disabled:opacity-50 text-indigo-400 hover:text-white"
        title={status === 'playing' ? 'Pause question' : 'Play question aloud'}
      >
        {status === 'loading' ? (
          <svg className="w-4 h-4 text-indigo-400 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
        ) : status === 'playing' ? (
          <svg className="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
          </svg>
        ) : (
          <svg className="w-4 h-4 text-indigo-400" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z" />
          </svg>
        )}
      </button>

      {/* Progress + label */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-indigo-300 font-medium">
            {status === 'loading'
              ? 'Synthesizing Audio...'
              : status === 'playing'
              ? 'Speaking Question...'
              : status === 'paused'
              ? 'Voice Paused'
              : 'AI Voice Ready'}
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            {isBrowserVoice ? 'Natural Voice' : voice}
          </span>
        </div>
        <div className="h-1 bg-indigo-950 rounded-full overflow-hidden">
          <div
            className="h-full bg-indigo-400 rounded-full transition-all duration-200"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Waveform animation when playing */}
      {status === 'playing' && (
        <div className="flex gap-0.5 items-end h-5 px-1">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="w-1 bg-indigo-400 rounded-full animate-pulse"
              style={{
                height: `${40 + (i % 2 === 0 ? 45 : 25)}%`,
                animationDelay: `${i * 0.15}s`,
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
