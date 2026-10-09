'use client'

import React, { useState } from 'react'
import {
  TrendingUp,
  BarChart2,
  Calendar,
  Layers,
  Award,
  ChevronDown,
} from 'lucide-react'

interface SkillCategory {
  category: string
  score: number
  tier: string
  delta: string
  color: string
}

const SKILL_METRICS: SkillCategory[] = [
  { category: 'System Architecture & Scaling', score: 92, tier: 'Top 5%', delta: '+6%', color: 'from-cyan-500 to-blue-500' },
  { category: 'Algorithms & Data Structures', score: 86, tier: 'Top 12%', delta: '+4%', color: 'from-violet-500 to-purple-500' },
  { category: 'Concurrency & Distributed Consensus', score: 79, tier: 'Top 22%', delta: '+8%', color: 'from-amber-500 to-orange-500' },
  { category: 'API Design & Resiliency (gRPC / REST)', score: 95, tier: 'Top 3%', delta: '+3%', color: 'from-emerald-500 to-teal-500' },
  { category: 'Executive Behavioral & STAR Format', score: 88, tier: 'Top 10%', delta: '+12%', color: 'from-pink-500 to-rose-500' },
]

export default function SkillHeatmap() {
  const [timeframe, setTimeframe] = useState<'week' | 'month' | 'year'>('month')
  const [showDropdown, setShowDropdown] = useState(false)

  // 6 points for SVG trend curve
  const points = [68, 72, 75, 81, 84, 88.4]
  const svgWidth = 500
  const svgHeight = 160
  const paddingX = 40
  const paddingY = 25

  const pointsCoordinates = points.map((p, idx) => {
    const x = paddingX + (idx / (points.length - 1)) * (svgWidth - paddingX * 2)
    const y = svgHeight - paddingY - ((p - 60) / 40) * (svgHeight - paddingY * 2)
    return { x, y, score: p }
  })

  const pathD = pointsCoordinates.reduce(
    (acc, curr, idx) => (idx === 0 ? `M ${curr.x} ${curr.y}` : `${acc} L ${curr.x} ${curr.y}`),
    ''
  )

  const areaD = `${pathD} L ${pointsCoordinates[pointsCoordinates.length - 1].x} ${svgHeight - 10} L ${pointsCoordinates[0].x} ${svgHeight - 10} Z`

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Skill Competency Heatmap (6 cols) */}
      <div className="lg:col-span-6 rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40">
        <div className="flex items-center justify-between mb-5 pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Competency Benchmark Radar</h3>
              <p className="text-xs text-slate-400">Staff SWE Rubric Calibration</p>
            </div>
          </div>
          <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
            Cohort: Top 8.4%
          </span>
        </div>

        <div className="space-y-4">
          {SKILL_METRICS.map((item, idx) => (
            <div key={idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">{item.category}</span>
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-bold text-emerald-400">{item.delta}</span>
                  <span className="text-[11px] font-medium text-slate-400 px-1.5 py-0.5 rounded bg-slate-800">
                    {item.tier}
                  </span>
                  <span className="font-bold text-white w-8 text-right">{item.score}%</span>
                </div>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800/80 overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${item.color} transition-all duration-700`}
                  style={{ width: `${item.score}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Historical Performance Trend Chart (6 cols) */}
      <div className="lg:col-span-6 rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-white">Skill Mastery Trajectory</h3>
              <p className="text-xs text-slate-400">Progressive Mock Interview Scores</p>
            </div>
          </div>

          {/* Timeframe Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowDropdown(!showDropdown)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-950 border border-slate-800 text-slate-300 hover:border-slate-700"
            >
              <Calendar className="w-3.5 h-3.5 text-cyan-400" />
              <span className="capitalize">{timeframe}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>

            {showDropdown && (
              <div className="absolute right-0 mt-1 w-28 rounded-xl bg-slate-900 border border-slate-800 shadow-xl z-20 py-1">
                {(['week', 'month', 'year'] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => {
                      setTimeframe(t)
                      setShowDropdown(false)
                    }}
                    className={`w-full text-left px-3 py-1.5 text-xs font-medium capitalize hover:bg-slate-800 ${
                      timeframe === t ? 'text-cyan-400 font-bold' : 'text-slate-300'
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* SVG Interactive Trend Visual */}
        <div className="w-full relative flex-1 flex flex-col justify-center">
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            className="w-full h-40 overflow-visible"
            preserveAspectRatio="none"
          >
            <defs>
              <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.25" />
                <stop offset="100%" stopColor="#06b6d4" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid lines */}
            {[40, 80, 120].map((y, i) => (
              <line
                key={i}
                x1={paddingX}
                y1={y}
                x2={svgWidth - paddingX}
                y2={y}
                stroke="#1e293b"
                strokeDasharray="4 4"
              />
            ))}

            {/* Area fill */}
            <path d={areaD} fill="url(#areaGradient)" />

            {/* Trend line */}
            <path d={pathD} fill="none" stroke="#06b6d4" strokeWidth="2.5" strokeLinecap="round" />

            {/* Point circles */}
            {pointsCoordinates.map((pt, i) => (
              <g key={i}>
                <circle cx={pt.x} cy={pt.y} r="4" fill="#0f172a" stroke="#22d3ee" strokeWidth="2" />
                <text
                  x={pt.x}
                  y={pt.y - 10}
                  fill="#94a3b8"
                  fontSize="10"
                  fontWeight="600"
                  textAnchor="middle"
                >
                  {pt.score}
                </text>
              </g>
            ))}
          </svg>

          <div className="flex items-center justify-between text-[11px] text-slate-500 px-6 pt-2 border-t border-slate-800/60">
            <span>Session 1</span>
            <span>Session 3</span>
            <span>Session 5</span>
            <span>Session 8</span>
            <span>Current (88.4)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
