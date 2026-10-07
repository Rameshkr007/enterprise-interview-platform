'use client'

import React, { useEffect, useRef } from 'react'

interface AIInterviewerAvatarProps {
  isSpeaking: boolean
  isListening: boolean
  difficulty?: string
  interviewerName?: string
}

export function AIInterviewerAvatar({
  isSpeaking,
  isListening,
  difficulty = 'medium',
  interviewerName = 'Aura AI',
}: AIInterviewerAvatarProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number
    let frame = 0

    const render = () => {
      frame++
      const width = canvas.width
      const height = canvas.height
      ctx.clearRect(0, 0, width, height)

      const centerX = width / 2
      const centerY = height / 2

      // Dynamic color theme based on difficulty
      let mainGlow = 'rgba(99, 102, 241, ' // Indigo
      let accentGlow = 'rgba(168, 85, 247, ' // Purple
      if (difficulty === 'hard' || difficulty === 'expert') {
        mainGlow = 'rgba(239, 68, 68, ' // Red
        accentGlow = 'rgba(249, 115, 22, ' // Orange
      } else if (difficulty === 'easy') {
        mainGlow = 'rgba(16, 185, 129, ' // Emerald
        accentGlow = 'rgba(6, 182, 212, ' // Cyan
      }

      // 1. Holographic background aura
      const pulseRate = isSpeaking ? 0.08 : isListening ? 0.04 : 0.02
      const pulse = Math.sin(frame * pulseRate) * 12
      const outerRadius = 85 + pulse

      const gradient = ctx.createRadialGradient(
        centerX,
        centerY,
        20,
        centerX,
        centerY,
        outerRadius + 30
      )
      gradient.addColorStop(0, mainGlow + '0.45)')
      gradient.addColorStop(0.5, accentGlow + '0.2)')
      gradient.addColorStop(1, 'rgba(15, 23, 42, 0)')

      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(centerX, centerY, outerRadius + 30, 0, Math.PI * 2)
      ctx.fill()

      // 2. Rotating orbital wave rings (audio visualization simulation)
      const ringCount = 3
      for (let i = 0; i < ringCount; i++) {
        ctx.save()
        ctx.translate(centerX, centerY)
        ctx.rotate((frame * (0.01 + i * 0.005) * (i % 2 === 0 ? 1 : -1)))

        ctx.beginPath()
        const ringR = outerRadius - 15 + i * 14
        const distortion = isSpeaking
          ? Math.sin(frame * 0.2 + i) * 6
          : isListening
          ? Math.cos(frame * 0.1 + i) * 3
          : 0

        ctx.arc(0, 0, Math.max(10, ringR + distortion), 0, Math.PI * 2)
        ctx.strokeStyle =
          i === 0
            ? mainGlow + '0.8)'
            : i === 1
            ? accentGlow + '0.6)'
            : 'rgba(255, 255, 255, 0.4)'
        ctx.lineWidth = 1.5
        ctx.setLineDash([8 + i * 4, 6 + i * 2])
        ctx.stroke()
        ctx.restore()
      }

      // 3. Central Stylized AI Core
      ctx.save()
      ctx.beginPath()
      const coreR = 50 + (isSpeaking ? Math.sin(frame * 0.15) * 4 : 0)
      ctx.arc(centerX, centerY, coreR, 0, Math.PI * 2)
      const coreGrad = ctx.createLinearGradient(
        centerX - coreR,
        centerY - coreR,
        centerX + coreR,
        centerY + coreR
      )
      coreGrad.addColorStop(0, '#1e1b4b')
      coreGrad.addColorStop(0.5, '#312e81')
      coreGrad.addColorStop(1, '#0f172a')
      ctx.fillStyle = coreGrad
      ctx.fill()
      ctx.strokeStyle = mainGlow + '0.9)'
      ctx.lineWidth = 2.5
      ctx.stroke()
      ctx.restore()

      // 4. Stylized Futuristic Digital Eyes
      const blink = Math.sin(frame * 0.03) > 0.96 ? 0.2 : 1
      const eyeSpacing = 18
      const eyeY = centerY - 5 + Math.sin(frame * 0.04) * 2

      ctx.fillStyle = '#38bdf8'
      ctx.shadowColor = '#38bdf8'
      ctx.shadowBlur = 10

      // Left Eye
      ctx.beginPath()
      ctx.ellipse(centerX - eyeSpacing, eyeY, 6, 8 * blink, 0, 0, Math.PI * 2)
      ctx.fill()

      // Right Eye
      ctx.beginPath()
      ctx.ellipse(centerX + eyeSpacing, eyeY, 6, 8 * blink, 0, 0, Math.PI * 2)
      ctx.fill()
      ctx.shadowBlur = 0

      // 5. Stylized Mouth / Audio Waveform Line
      ctx.beginPath()
      const mouthY = centerY + 22
      const mouthWidth = 24
      if (isSpeaking) {
        ctx.moveTo(centerX - mouthWidth / 2, mouthY)
        for (let x = -mouthWidth / 2; x <= mouthWidth / 2; x += 3) {
          const wave = Math.sin(frame * 0.3 + x * 0.5) * 6
          ctx.lineTo(centerX + x, mouthY + wave)
        }
        ctx.strokeStyle = '#a855f7'
        ctx.lineWidth = 2.5
        ctx.stroke()
      } else {
        ctx.moveTo(centerX - 10, mouthY)
        ctx.lineTo(centerX + 10, mouthY)
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)'
        ctx.lineWidth = 2
        ctx.stroke()
      }

      animationFrameId = requestAnimationFrame(render)
    }

    render()

    return () => {
      cancelAnimationFrame(animationFrameId)
    }
  }, [isSpeaking, isListening, difficulty])

  return (
    <div className="relative flex flex-col items-center justify-center p-4 rounded-2xl glass-card border border-white/10 overflow-hidden bg-slate-900/60 shadow-2xl">
      <div className="absolute top-3 left-4 flex items-center gap-2">
        <span
          className={`w-2.5 h-2.5 rounded-full ${
            isSpeaking
              ? 'bg-purple-500 animate-pulse'
              : isListening
              ? 'bg-emerald-400 animate-ping'
              : 'bg-indigo-400'
          }`}
        />
        <span className="text-xs font-semibold tracking-wider text-slate-300 uppercase">
          {isSpeaking ? 'Speaking' : isListening ? 'Listening' : 'Ready'}
        </span>
      </div>

      <div className="absolute top-3 right-4">
        <span className="text-xs px-2.5 py-0.5 rounded-full bg-white/5 border border-white/10 text-slate-400 capitalize">
          Difficulty: {difficulty}
        </span>
      </div>

      <canvas
        ref={canvasRef}
        width={260}
        height={260}
        className="w-[200px] h-[200px] sm:w-[240px] sm:h-[240px]"
      />

      <div className="mt-2 text-center">
        <h4 className="text-sm font-bold text-white tracking-wide">{interviewerName}</h4>
        <p className="text-xs text-slate-400">Adaptive State Engine • LangGraph</p>
      </div>
    </div>
  )
}
