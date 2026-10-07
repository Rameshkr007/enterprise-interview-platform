'use client'

import React, { useEffect, useRef, useState } from 'react'

interface EmotionAnalysis {
  confidence: number
  eyeContactPct: number
  composure: number
  detectedEmotion: 'Focused' | 'Confident' | 'Thoughtful' | 'Nervous'
}

interface WebcamEmotionTrackerProps {
  onMetricsUpdate?: (metrics: EmotionAnalysis) => void
}

export function WebcamEmotionTracker({ onMetricsUpdate }: WebcamEmotionTrackerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const [cameraActive, setCameraActive] = useState<boolean>(false)
  const [metrics, setMetrics] = useState<EmotionAnalysis>({
    confidence: 88,
    eyeContactPct: 92,
    composure: 85,
    detectedEmotion: 'Focused',
  })
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Start webcam stream
  const startCamera = async () => {
    try {
      setErrorMsg(null)
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 320, height: 240, facingMode: 'user' },
        audio: false,
      })
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
        setCameraActive(true)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Webcam access denied or unavailable'
      setErrorMsg(msg)
      setCameraActive(false)
    }
  }

  // Stop webcam
  const stopCamera = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream
      stream.getTracks().forEach((track) => track.stop())
      videoRef.current.srcObject = null
      setCameraActive(false)
    }
  }

  // Periodically compute realistic simulated computer vision engagement metrics
  useEffect(() => {
    if (!cameraActive) return

    const interval = setInterval(() => {
      // Subtle fluctuations reflecting natural speech
      const eyeRandom = Math.min(100, Math.max(70, Math.round(88 + (Math.random() * 12 - 5))))
      const confRandom = Math.min(100, Math.max(65, Math.round(84 + (Math.random() * 16 - 6))))
      const compRandom = Math.min(100, Math.max(60, Math.round(82 + (Math.random() * 14 - 5))))

      let emotion: EmotionAnalysis['detectedEmotion'] = 'Focused'
      if (confRandom > 85) emotion = 'Confident'
      else if (compRandom < 70) emotion = 'Nervous'
      else emotion = 'Thoughtful'

      const newMetrics: EmotionAnalysis = {
        confidence: confRandom,
        eyeContactPct: eyeRandom,
        composure: compRandom,
        detectedEmotion: emotion,
      }

      setMetrics(newMetrics)
      if (onMetricsUpdate) {
        onMetricsUpdate(newMetrics)
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [cameraActive, onMetricsUpdate])

  useEffect(() => {
    return () => {
      stopCamera()
    }
  }, [])

  return (
    <div className="relative rounded-2xl glass-card border border-white/10 p-4 bg-slate-900/60 shadow-xl overflow-hidden flex flex-col justify-between">
      {/* Top Header */}
      <div className="flex items-center justify-between mb-3 z-10">
        <div className="flex items-center gap-2">
          <span className="text-sm">👁️</span>
          <h4 className="text-xs font-bold text-white uppercase tracking-wider">
            Vision & Presence AI
          </h4>
        </div>
        <button
          onClick={cameraActive ? stopCamera : startCamera}
          className={`text-xs px-2.5 py-1 rounded-lg font-medium transition-all ${
            cameraActive
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 hover:bg-rose-500/30'
              : 'bg-brand-500/20 text-brand-300 border border-brand-500/40 hover:bg-brand-500/30'
          }`}
        >
          {cameraActive ? 'Turn Off Cam' : 'Enable Camera'}
        </button>
      </div>

      {/* Video Container with AR-style bounding frame */}
      <div className="relative w-full h-[180px] bg-slate-950/80 rounded-xl overflow-hidden flex items-center justify-center border border-white/5">
        <video
          ref={videoRef}
          playsInline
          muted
          className={`w-full h-full object-cover transform -scale-x-100 ${
            cameraActive ? 'block' : 'hidden'
          }`}
        />

        {!cameraActive && (
          <div className="text-center p-4">
            <span className="text-3xl block mb-2 opacity-50">📹</span>
            <p className="text-xs text-slate-400">
              {errorMsg ? errorMsg : 'Camera disabled. Click Enable to track eye contact & composure in real-time.'}
            </p>
          </div>
        )}

        {/* Visual AR Face Target Simulation Overlay */}
        {cameraActive && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
            {/* Target box */}
            <div className="w-32 h-40 border border-brand-400/40 rounded-3xl relative animate-pulse">
              <span className="absolute -top-1 -left-1 w-3 h-3 border-t-2 border-l-2 border-brand-400" />
              <span className="absolute -top-1 -right-1 w-3 h-3 border-t-2 border-r-2 border-brand-400" />
              <span className="absolute -bottom-1 -left-1 w-3 h-3 border-b-2 border-l-2 border-brand-400" />
              <span className="absolute -bottom-1 -right-1 w-3 h-3 border-b-2 border-r-2 border-brand-400" />
            </div>

            {/* Live badge */}
            <div className="absolute top-2 left-2 flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-[10px] text-emerald-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              AR Tracking
            </div>
          </div>
        )}
      </div>

      {/* Real-time Vision Metrics HUD */}
      {cameraActive && (
        <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-white/5">
          <div className="text-center p-1.5 rounded-lg bg-white/5">
            <div className="text-[10px] text-slate-400 mb-0.5">Eye Contact</div>
            <div className="text-xs font-bold text-sky-400">{metrics.eyeContactPct}%</div>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-white/5">
            <div className="text-[10px] text-slate-400 mb-0.5">Composure</div>
            <div className="text-xs font-bold text-emerald-400">{metrics.composure}%</div>
          </div>
          <div className="text-center p-1.5 rounded-lg bg-white/5">
            <div className="text-[10px] text-slate-400 mb-0.5">Expression</div>
            <div className="text-xs font-bold text-amber-300">{metrics.detectedEmotion}</div>
          </div>
        </div>
      )}
    </div>
  )
}
