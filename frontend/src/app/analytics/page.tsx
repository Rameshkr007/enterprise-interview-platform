'use client'

import React, { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import Link from 'next/link'
import {
  TrendingUp,
  Award,
  Users,
  Flame,
  Clock,
  ArrowRight,
  DollarSign,
  BarChart3,
  Layers,
  ShieldCheck,
  AlertCircle,
  CheckCircle2,
  Briefcase,
  Sliders,
  Zap,
} from 'lucide-react'
import { api, enterpriseAnalyticsApi } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import type {
  TalentSupplyDemandResponse,
  EnterpriseRoiMetrics,
} from '@/lib/types'

interface ProgressData {
  total_sessions: number
  avg_score: number
  best_score: number
  score_history: Array<{ date: string; score: number; session_id: string }>
  skill_heatmap: Record<string, { avg_score: number; total_turns: number }>
  badges: Array<{ id: string; name: string; icon: string; earned: boolean }>
  streak_days: number
  weak_categories: string[]
  strong_categories: string[]
}

interface LeaderboardData {
  leaderboard: Array<{
    rank: number
    user_name: string
    avg_score: number
    best_score: number
    session_count: number
    percentile: number
    is_current_user: boolean
  }>
  my_rank: { rank: number | null; avg_score: number; percentile: number }
  total_participants: number
}

function ScoreLine({ history }: { history: ProgressData['score_history'] }) {
  if (history.length === 0) return <p className="text-slate-500 text-sm">No sessions yet</p>
  const max = 100
  const w = 400
  const h = 100
  const points = history
    .map((item, i) => {
      const x = (i / Math.max(history.length - 1, 1)) * w
      const y = h - (item.score / max) * h
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')

  return (
    <div className="overflow-x-auto">
      <svg viewBox={`0 0 ${w} ${h}`} className="w-full" style={{ maxHeight: 120 }}>
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#6366f1" stopOpacity="0.3" />
            <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
          </linearGradient>
        </defs>
        <polyline points={points + ` ${w},${h} 0,${h}`} fill="url(#scoreGrad)" stroke="none" />
        <polyline points={points} fill="none" stroke="#6366f1" strokeWidth="2" strokeLinejoin="round" />
        {history.map((item, i) => {
          const x = (i / Math.max(history.length - 1, 1)) * w
          const y = h - (item.score / max) * h
          return (
            <circle key={i} cx={x} cy={y} r="3" fill="#818cf8" className="cursor-pointer">
              <title>
                Session {i + 1}: {item.score.toFixed(1)}
              </title>
            </circle>
          )
        })}
      </svg>
    </div>
  )
}

const SHORTAGE_BADGES = {
  critical: { label: 'Critical Shortage', bg: 'bg-rose-500/10 text-rose-400 border-rose-500/30' },
  moderate: { label: 'Moderate Shortage', bg: 'bg-amber-500/10 text-amber-400 border-amber-500/30' },
  balanced: { label: 'Balanced Supply', bg: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30' },
  surplus: { label: 'Surplus Supply', bg: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30' },
}

export default function AnalyticsPage() {
  const { user } = useAuthStore()
  const [activeTab, setActiveTab] = useState<'personal' | 'enterprise_bi'>('personal')

  // Personal queries
  const { data: progress, isLoading: progLoading } = useQuery<ProgressData>({
    queryKey: ['analytics-progress'],
    queryFn: () => api.get('/analytics/progress').then((r) => r.data),
    enabled: !!user,
  })

  const { data: leaderboard, isLoading: lbLoading } = useQuery<LeaderboardData>({
    queryKey: ['analytics-leaderboard'],
    queryFn: () => api.get('/analytics/leaderboard').then((r) => r.data),
    enabled: !!user,
  })

  // Enterprise BI queries (Phase 16)
  const { data: supplyDemand, isLoading: sdLoading } = useQuery<TalentSupplyDemandResponse>({
    queryKey: ['enterprise-supply-demand'],
    queryFn: () => enterpriseAnalyticsApi.getSupplyDemand(),
  })

  const { data: roiMetrics, isLoading: roiLoading } = useQuery<EnterpriseRoiMetrics>({
    queryKey: ['enterprise-roi-metrics'],
    queryFn: () => enterpriseAnalyticsApi.getRoiMetrics(),
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-bold">
                <BarChart3 className="w-5 h-5" />
              </div>
              <div>
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                  Analytics & Talent Intelligence
                </h1>
                <p className="text-sm text-slate-400">
                  Candidate performance progression, skill supply vs demand & platform executive ROI
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs font-semibold">
              <button
                onClick={() => setActiveTab('personal')}
                className={`px-3 py-1.5 rounded-lg transition ${
                  activeTab === 'personal'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                Candidate Progress
              </button>
              <button
                onClick={() => setActiveTab('enterprise_bi')}
                className={`px-3 py-1.5 rounded-lg transition flex items-center gap-1.5 ${
                  activeTab === 'enterprise_bi'
                    ? 'bg-indigo-600 text-white'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Zap className="w-3.5 h-3.5 text-amber-400" />
                Enterprise Talent BI
              </button>
            </div>
            <Link
              href="/dashboard"
              className="px-3.5 py-1.5 text-xs font-medium rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 transition"
            >
              ← Dashboard
            </Link>
          </div>
        </div>

        {/* TAB 1: PERSONAL CANDIDATE ANALYTICS */}
        {activeTab === 'personal' && (
          <div className="space-y-6">
            {/* Stats Row */}
            {progLoading ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-24 bg-slate-900/50 border border-slate-800 rounded-2xl animate-pulse" />
                ))}
              </div>
            ) : (
              progress && (
                <>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[
                      { label: 'Total Sessions', value: progress.total_sessions, suffix: '' },
                      { label: 'Average Score', value: progress.avg_score.toFixed(1), suffix: '/100' },
                      { label: 'Best Score', value: progress.best_score.toFixed(1), suffix: '/100' },
                      { label: 'Day Streak', value: progress.streak_days, suffix: '🔥' },
                    ].map((s) => (
                      <div key={s.label} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                        <div className="text-2xl font-extrabold text-white mb-1">
                          {s.value}
                          <span className="text-sm text-slate-400 ml-1">{s.suffix}</span>
                        </div>
                        <div className="text-xs text-slate-400">{s.label}</div>
                      </div>
                    ))}
                  </div>

                  {/* Score Trend */}
                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
                    <h2 className="text-lg font-bold text-white mb-4">Score Trend Across Sessions</h2>
                    <ScoreLine history={progress.score_history} />
                  </div>

                  {/* Heatmap + Badges */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
                      <h2 className="text-lg font-bold text-white mb-4">Skill Heatmap</h2>
                      <div className="space-y-3">
                        {Object.entries(progress.skill_heatmap).map(([cat, data]) => (
                          <div key={cat}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className="text-slate-300 capitalize">{cat.replace('_', ' ')}</span>
                              <span className="text-white font-semibold">
                                {(data.avg_score * 100).toFixed(0)}% ({data.total_turns} turns)
                              </span>
                            </div>
                            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                              <div
                                className="h-full rounded-full"
                                style={{
                                  width: `${data.avg_score * 100}%`,
                                  background:
                                    data.avg_score > 0.7
                                      ? '#10b981'
                                      : data.avg_score > 0.5
                                      ? '#f59e0b'
                                      : '#ef4444',
                                }}
                              />
                            </div>
                          </div>
                        ))}
                        {Object.keys(progress.skill_heatmap).length === 0 && (
                          <p className="text-slate-500 text-sm">Complete sessions to see skill breakdown</p>
                        )}
                      </div>
                    </div>

                    <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
                      <h2 className="text-lg font-bold text-white mb-4">Badges Earned</h2>
                      <div className="flex flex-wrap gap-2.5">
                        {progress.badges.map((b) => (
                          <div
                            key={b.id}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-semibold ${
                              b.earned
                                ? 'bg-indigo-500/20 border-indigo-500/40 text-indigo-300'
                                : 'bg-slate-950 border-slate-800 text-slate-600'
                            }`}
                          >
                            <span>{b.icon}</span>
                            <span>{b.name}</span>
                          </div>
                        ))}
                      </div>

                      <div className="mt-6 pt-4 border-t border-slate-800">
                        <h3 className="text-xs font-semibold uppercase text-slate-400 tracking-wider mb-2">
                          Focus Areas
                        </h3>
                        <div className="space-y-2">
                          {progress.weak_categories.map((cat) => (
                            <div key={cat} className="flex items-center gap-2 text-xs">
                              <span className="text-rose-400">↓</span>
                              <span className="text-slate-300 capitalize font-medium">{cat.replace('_', ' ')}</span>
                              <span className="text-slate-500">needs practice</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )
            )}

            {/* Leaderboard */}
            <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <Award className="w-5 h-5 text-amber-400" />
                  Global Leaderboard
                </h2>
                {leaderboard && (
                  <div className="text-right text-xs">
                    <div className="text-white font-bold">Your Rank: #{leaderboard.my_rank.rank ?? '—'}</div>
                    <div className="text-slate-400">Top {leaderboard.my_rank.percentile.toFixed(0)}%</div>
                  </div>
                )}
              </div>

              {lbLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-12 bg-slate-950 rounded-xl animate-pulse" />
                  ))}
                </div>
              ) : (
                leaderboard && (
                  <div className="space-y-2">
                    {leaderboard.leaderboard.map((entry) => (
                      <div
                        key={entry.rank}
                        className={`flex items-center gap-4 p-3.5 rounded-xl border transition-all ${
                          entry.is_current_user
                            ? 'bg-indigo-600/15 border-indigo-500/40 text-indigo-100'
                            : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                        }`}
                      >
                        <div
                          className={`w-8 text-center font-bold text-sm ${
                            entry.rank === 1
                              ? 'text-yellow-400'
                              : entry.rank === 2
                              ? 'text-slate-300'
                              : entry.rank === 3
                              ? 'text-amber-600'
                              : 'text-slate-500'
                          }`}
                        >
                          {entry.rank <= 3 ? ['🥇', '🥈', '🥉'][entry.rank - 1] : `#${entry.rank}`}
                        </div>
                        <div className="flex-1">
                          <div className="text-white text-sm font-medium">
                            {entry.user_name}{' '}
                            {entry.is_current_user && (
                              <span className="text-indigo-400 text-xs ml-1">(you)</span>
                            )}
                          </div>
                          <div className="text-slate-500 text-xs">
                            {entry.session_count} sessions • Top {(100 - entry.percentile).toFixed(0)}%
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-white font-bold text-sm">{entry.avg_score.toFixed(1)}</div>
                          <div className="text-slate-500 text-xs">avg score</div>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              )}
            </div>
          </div>
        )}

        {/* TAB 2: ENTERPRISE TALENT BI (PHASE 16) */}
        {activeTab === 'enterprise_bi' && (
          <div className="space-y-8">
            {/* ROI & Executive Value Cards */}
            {roiLoading ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-28 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
                ))}
              </div>
            ) : (
              roiMetrics && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <DollarSign className="w-5 h-5 text-emerald-400" />
                        Executive Platform ROI & Value Metrics
                      </h3>
                      <p className="text-xs text-slate-400">
                        Quantified recruiter capacity savings & AI efficiency multipliers.
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-bold">
                      {roiMetrics.net_roi_multiple.toFixed(1)}x Net ROI
                    </span>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Recruiter Hours Saved</div>
                      <div className="text-2xl font-extrabold text-indigo-400 mt-1">
                        {roiMetrics.recruiter_hours_saved.toFixed(1)} hrs
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">2.5 hrs/automated session</div>
                    </div>

                    <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                      <div className="text-[10px] uppercase font-bold text-emerald-400">Cost Savings (USD)</div>
                      <div className="text-2xl font-extrabold text-emerald-400 mt-1">
                        ${roiMetrics.cost_savings_usd.toLocaleString()}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">@ $75/hr blended capacity</div>
                    </div>

                    <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                      <div className="text-[10px] uppercase font-bold text-blue-400">Candidate Score Lift</div>
                      <div className="text-2xl font-extrabold text-blue-400 mt-1">
                        +{roiMetrics.avg_candidate_score_lift.toFixed(1)} pts
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">via 7-day learning plans</div>
                    </div>

                    <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                      <div className="text-[10px] uppercase font-bold text-purple-400">Time-to-Fill Reduction</div>
                      <div className="text-2xl font-extrabold text-purple-400 mt-1">
                        -{roiMetrics.time_to_fill_reduction_pct}%
                      </div>
                      <div className="text-[10px] text-slate-500 mt-0.5">faster candidate pipeline</div>
                    </div>
                  </div>

                  {/* Department Velocity Breakdown */}
                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                    <h4 className="text-sm font-bold uppercase tracking-wider text-slate-400">
                      Department Velocity & Satisfaction Breakdown
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      {Object.entries(roiMetrics.department_metrics).map(([dept, data]) => (
                        <div key={dept} className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2">
                          <div className="font-bold text-sm text-slate-200">{dept}</div>
                          <div className="text-xs text-slate-400 flex justify-between">
                            <span>Interviews:</span>
                            <span className="text-white font-semibold">{data.interviews}</span>
                          </div>
                          <div className="text-xs text-slate-400 flex justify-between">
                            <span>Avg Time-to-Fill:</span>
                            <span className="text-indigo-400 font-semibold">{data.time_to_fill_days} days</span>
                          </div>
                          <div className="text-xs text-slate-400 flex justify-between">
                            <span>Satisfaction:</span>
                            <span className="text-emerald-400 font-semibold">★ {data.satisfaction_score}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )
            )}

            {/* Talent Supply vs Demand Intelligence */}
            {sdLoading ? (
              <div className="h-64 bg-slate-900 border border-slate-800 rounded-2xl animate-pulse" />
            ) : (
              supplyDemand && (
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                    <div>
                      <h3 className="text-lg font-bold text-white flex items-center gap-2">
                        <Briefcase className="w-5 h-5 text-indigo-400" />
                        Talent Supply vs. Requisition Demand Matrix
                      </h3>
                      <p className="text-xs text-slate-400">
                        {supplyDemand.total_skills_tracked} skills analyzed against candidate verified masteries & requisition requirements.
                      </p>
                    </div>
                    {supplyDemand.critical_shortage_count > 0 && (
                      <span className="px-3 py-1 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold flex items-center gap-1.5 self-start md:self-auto">
                        <AlertCircle className="w-3.5 h-3.5" />
                        {supplyDemand.critical_shortage_count} Critical Shortages Detected
                      </span>
                    )}
                  </div>

                  <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-950/60">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-950 text-xs text-slate-400 uppercase tracking-wider">
                          <th className="p-4">Skill Domain</th>
                          <th className="p-4">Supply (Candidates)</th>
                          <th className="p-4">Demand (Requisitions)</th>
                          <th className="p-4">Supply / Demand Ratio</th>
                          <th className="p-4">Shortage Status</th>
                          <th className="p-4 text-right">Proj. Time-to-Fill</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {supplyDemand.skills.map((item) => {
                          const badge = SHORTAGE_BADGES[item.shortage_level] || SHORTAGE_BADGES.balanced
                          return (
                            <tr key={item.skill_name} className="hover:bg-slate-800/30 transition">
                              <td className="p-4 font-semibold text-slate-200 capitalize">
                                {item.skill_name.replace('-', ' ')}
                              </td>
                              <td className="p-4 text-slate-300 font-bold">{item.candidate_supply_count}</td>
                              <td className="p-4 text-slate-300 font-bold">{item.requisition_demand_count}</td>
                              <td className="p-4">
                                <div className="flex items-center gap-3">
                                  <div className="w-24 bg-slate-800 rounded-full h-2.5 overflow-hidden">
                                    <div
                                      className={`h-full rounded-full ${
                                        item.supply_demand_ratio < 0.5
                                          ? 'bg-rose-500'
                                          : item.supply_demand_ratio < 1.0
                                          ? 'bg-amber-500'
                                          : 'bg-emerald-500'
                                      }`}
                                      style={{ width: `${Math.min(item.supply_demand_ratio * 50, 100)}%` }}
                                    />
                                  </div>
                                  <span className="font-mono text-xs font-bold text-slate-300">
                                    {item.supply_demand_ratio.toFixed(2)}x
                                  </span>
                                </div>
                              </td>
                              <td className="p-4">
                                <span className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${badge.bg}`}>
                                  {badge.label}
                                </span>
                              </td>
                              <td className="p-4 text-right font-bold text-slate-200">
                                {item.projected_time_to_fill_days} days
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )
            )}
          </div>
        )}
      </div>
    </div>
  )
}
