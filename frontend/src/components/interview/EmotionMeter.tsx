'use client'
import { useEffect, useRef, useState } from 'react'

interface EmotionMeterProps {
  silenceRatio: number
  pitchVarianceScore: number
  fillerWordRate: number
  speechRateWpm: number
}

interface Metric {
  label: string
  value: number
  ideal: string
  color: string
  description: string
}

function GaugeBar({ value, color, label }: { value: number; color: string; label: string }) {
  const pct = Math.min(Math.max(value, 0), 100)
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-white font-medium">{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{ width: `${pct}%`, background: color }}
        />
      </div>
    </div>
  )
}

export function EmotionMeter({
  silenceRatio,
  pitchVarianceScore,
  fillerWordRate,
  speechRateWpm,
}: EmotionMeterProps) {
  // Derived scores (0–100)
  const confidenceScore = Math.round(
    (1 - silenceRatio * 0.3 - pitchVarianceScore * 0.3 - Math.min(fillerWordRate / 20, 1) * 0.4) * 100
  )
  const clarityScore = Math.round(
    (1 - Math.min(fillerWordRate / 15, 1) * 0.6 - silenceRatio * 0.4) * 100
  )
  const fluencyScore = Math.round(
    Math.max(0, 1 - Math.abs(speechRateWpm - 140) / 100) * 100
  )

  const metrics: Metric[] = [
    {
      label: 'Confidence',
      value: Math.max(0, confidenceScore),
      ideal: '> 70',
      color: confidenceScore > 70 ? '#10b981' : confidenceScore > 50 ? '#f59e0b' : '#ef4444',
      description: 'Based on pitch stability & pause patterns',
    },
    {
      label: 'Clarity',
      value: Math.max(0, clarityScore),
      ideal: '> 75',
      color: clarityScore > 75 ? '#10b981' : clarityScore > 55 ? '#f59e0b' : '#ef4444',
      description: 'Filler word frequency & silence ratio',
    },
    {
      label: 'Fluency',
      value: Math.max(0, fluencyScore),
      ideal: '120–160 WPM',
      color: fluencyScore > 70 ? '#10b981' : fluencyScore > 50 ? '#f59e0b' : '#ef4444',
      description: `Current: ${Math.round(speechRateWpm)} WPM`,
    },
  ]

  return (
    <div className="glass-card p-5 space-y-5">
      <div className="flex items-center gap-2">
        <span className="text-lg">🧠</span>
        <h3 className="text-sm font-semibold text-white">Real-time Delivery Analytics</h3>
      </div>

      <div className="space-y-4">
        {metrics.map((m) => (
          <div key={m.label}>
            <GaugeBar value={m.value} color={m.color} label={m.label} />
            <p className="text-xs text-slate-500 mt-1">{m.description}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-white/5">
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">Silence Ratio</div>
          <div className={`text-sm font-bold ${silenceRatio > 0.5 ? 'text-red-400' : silenceRatio > 0.3 ? 'text-amber-400' : 'text-green-400'}`}>
            {(silenceRatio * 100).toFixed(1)}%
          </div>
        </div>
        <div className="text-center">
          <div className="text-xs text-slate-500 mb-1">Filler/min</div>
          <div className={`text-sm font-bold ${fillerWordRate > 10 ? 'text-red-400' : fillerWordRate > 5 ? 'text-amber-400' : 'text-green-400'}`}>
            {fillerWordRate.toFixed(1)}
          </div>
        </div>
      </div>
    </div>
  )
}
