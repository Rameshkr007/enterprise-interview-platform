'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  TrendingUp,
  Award,
  Mic,
  Code2,
  Cpu,
  Users,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  RefreshCw,
  Sparkles,
  ArrowUpRight,
  BookOpen,
  X,
  Target,
  BarChart2,
  GitCommit,
  Layers,
  ShieldCheck,
  Zap,
  Sliders,
  ExternalLink,
} from 'lucide-react'
import { twinApi } from '@/lib/api'
import type { CandidateTwin, ExplainScoreResult, TwinBenchmark, TwinHistoryEvent } from '@/lib/types'

export default function CandidateTwinPage() {
  const [twin, setTwin] = useState<CandidateTwin | null>(null)
  const [benchmarks, setBenchmarks] = useState<TwinBenchmark | null>(null)
  const [historyEvents, setHistoryEvents] = useState<TwinHistoryEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'calibration' | 'trajectory' | 'benchmarks'>('overview')
  const [historyFilter, setHistoryFilter] = useState<string>('all')
  const [activeExplainDimension, setActiveExplainDimension] = useState<string | null>(null)
  const [explainData, setExplainData] = useState<ExplainScoreResult | null>(null)
  const [explainLoading, setExplainLoading] = useState(false)

  const loadTwinData = async () => {
    try {
      setLoading(true)
      setError(null)
      const [twinData, benchData] = await Promise.allSettled([
        twinApi.getMyTwin(),
        twinApi.getBenchmarks(),
      ])

      if (twinData.status === 'fulfilled') {
        setTwin(twinData.value)
        setHistoryEvents(twinData.value.historical_trajectory || [])
      } else {
        throw new Error(twinData.reason?.message || 'Failed to load Candidate AI Twin')
      }

      if (benchData.status === 'fulfilled') {
        setBenchmarks(benchData.value)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load Candidate AI Twin'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleSyncTwin = async () => {
    try {
      setSyncing(true)
      const [syncedTwin, benchData] = await Promise.all([
        twinApi.syncTwin(),
        twinApi.getBenchmarks(),
      ])
      setTwin(syncedTwin)
      setHistoryEvents(syncedTwin.historical_trajectory || [])
      setBenchmarks(benchData)
    } catch (err: unknown) {
      console.error('Twin sync failed:', err)
    } finally {
      setSyncing(false)
    }
  }

  const handleFilterHistory = async (filter: string) => {
    setHistoryFilter(filter)
    try {
      const events = await twinApi.getHistory(filter === 'all' ? undefined : filter)
      setHistoryEvents(events)
    } catch (err: unknown) {
      console.error('Filter history failed:', err)
    }
  }

  useEffect(() => {
    loadTwinData()
  }, [])

  const handleExplain = async (dimension: string) => {
    try {
      setActiveExplainDimension(dimension)
      setExplainLoading(true)
      const data = await twinApi.explainScore(dimension)
      setExplainData(data)
    } catch (err: unknown) {
      console.error('Explain score error:', err)
    } finally {
      setExplainLoading(false)
    }
  }

  const closeExplain = () => {
    setActiveExplainDimension(null)
    setExplainData(null)
  }

  const readinessColor = (score: number) => {
    if (score >= 80) return 'text-emerald-400 border-emerald-500/30 bg-emerald-500/10'
    if (score >= 65) return 'text-blue-400 border-blue-500/30 bg-blue-500/10'
    if (score >= 50) return 'text-amber-400 border-amber-500/30 bg-amber-500/10'
    return 'text-rose-400 border-rose-500/30 bg-rose-500/10'
  }

  const velocityStatusColor = (status: string) => {
    switch (status) {
      case 'accelerating':
        return 'text-emerald-400 bg-emerald-950/60 border-emerald-800'
      case 'steady':
        return 'text-blue-400 bg-blue-950/60 border-blue-800'
      case 'plateauing':
        return 'text-amber-400 bg-amber-950/60 border-amber-800'
      default:
        return 'text-rose-400 bg-rose-950/60 border-rose-800'
    }
  }

  const dagCalibration = twin?.technical_mastery?.dag_calibration || {
    total_skills_evaluated: 0,
    verified_skills_count: 0,
    avg_dag_score: 0,
    highest_tier_verified: 1,
  }

  const sm2Stability = twin?.technical_mastery?.sm2_memory_stability || {
    total_cards: 0,
    mature_cards_count: 0,
    average_retention_pct: 85.0,
    stability_status: 'moderate',
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header Breadcrumb & Actions */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium mb-1">
              <Brain className="w-4 h-4" />
              <span>Phase 14: Candidate AI Twin & History</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Candidate AI Twin & Longitudinal Profile
              <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-normal">
                Continuous Telemetry
              </span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Multi-source synthesis across STAR interviews, Python sandbox execution, verified Skill DAG mastery, and SM-2 memory retention.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={handleSyncTwin}
              disabled={syncing || loading}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-2 shadow-sm"
            >
              <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin text-cyan-400' : ''}`} />
              {syncing ? 'Recalibrating...' : 'Sync Twin'}
            </button>
            <Link
              href="/skills"
              className="px-3.5 py-2 text-sm font-medium rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700/80 transition flex items-center gap-1.5"
            >
              <Layers className="w-4 h-4 text-indigo-400" />
              <span>Skill DAG</span>
            </Link>
            <Link
              href="/learning"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-950 transition flex items-center gap-2"
            >
              <BookOpen className="w-4 h-4" />
              <span>SM-2 Studio</span>
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
            <p className="text-sm">Synthesizing twin profile across interview & memory modalities...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-300 space-y-3">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
              <span>Unable to Load Candidate Twin</span>
            </div>
            <p className="text-sm text-rose-300/80">{error}</p>
            <button
              onClick={loadTwinData}
              className="text-xs px-3 py-1.5 rounded-md bg-rose-900/60 hover:bg-rose-900 border border-rose-700 text-rose-200"
            >
              Retry
            </button>
          </div>
        ) : !twin ? (
          <div className="p-12 text-center rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
            <Brain className="w-12 h-12 text-slate-600 mx-auto" />
            <h3 className="text-lg font-medium text-slate-300">No Candidate Twin Established Yet</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              Complete your first interview session or take a skill assessment to initialize your continuous AI Twin profile.
            </p>
            <Link
              href="/interview/new"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium transition"
            >
              Start Diagnostic Interview
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        ) : (
          <>
            {/* Top Readiness Score & Growth Velocity Banner */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Overall Readiness Card */}
              <div className="lg:col-span-2 p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 relative overflow-hidden flex flex-col justify-between">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      Enterprise Composite Readiness
                    </span>
                    <h2 className="text-2xl font-bold text-white mt-1">Overall Interview Readiness</h2>
                    <p className="text-xs text-slate-400 mt-1">
                      Calibrated across 5 technical, coding, speech, and memory pillars.
                    </p>
                  </div>
                  <button
                    onClick={() => handleExplain('readiness')}
                    className="flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 bg-cyan-950/60 hover:bg-cyan-900/60 border border-cyan-800/60 px-3 py-1.5 rounded-lg transition"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Explain Score</span>
                  </button>
                </div>

                <div className="mt-6 flex items-baseline gap-4">
                  <div className="text-6xl font-black tracking-tight text-white">
                    {Math.round(twin.overall_readiness_score)}
                    <span className="text-2xl font-light text-slate-500">/100</span>
                  </div>
                  <div className={`px-3 py-1 rounded-full text-xs font-semibold border ${readinessColor(twin.overall_readiness_score)}`}>
                    {twin.overall_readiness_score >= 85
                      ? 'Bar Raiser / L5+ Offer Ready'
                      : twin.overall_readiness_score >= 70
                      ? 'Interview Ready'
                      : twin.overall_readiness_score >= 50
                      ? 'In Active Progression'
                      : 'Foundational Focus Required'}
                  </div>
                </div>

                <div className="mt-4">
                  <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                    <div
                      className="bg-gradient-to-r from-cyan-500 via-blue-500 to-indigo-500 h-2.5 rounded-full transition-all duration-1000"
                      style={{ width: `${Math.min(100, Math.max(0, twin.overall_readiness_score))}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-1.5">
                    <span>Baseline: 50</span>
                    <span>Ready: 70</span>
                    <span>Bar Raiser: 85+</span>
                  </div>
                </div>
              </div>

              {/* Growth Velocity */}
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      Growth Velocity
                    </span>
                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-4xl font-bold text-emerald-400">
                      {twin.growth_velocity > 0 ? `+${twin.growth_velocity.toFixed(2)}` : twin.growth_velocity.toFixed(2)}
                    </span>
                    <span className="text-xs text-slate-400">pts / milestone</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">
                    OLS linear regression slope calculated across your verified timeline.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
                  <span>Trajectory Status</span>
                  <span
                    className={`font-semibold capitalize px-2 py-0.5 rounded border text-[11px] ${
                      benchmarks ? velocityStatusColor(benchmarks.growth_velocity_status) : 'text-emerald-400 border-emerald-800/40'
                    }`}
                  >
                    {benchmarks?.growth_velocity_status || 'Steady'}
                  </span>
                </div>
              </div>

              {/* Speech & Audio Telemetry */}
              <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      Communication Signals
                    </span>
                    <Mic className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="mt-3 space-y-2 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Pace:</span>
                      <span className="font-semibold text-slate-200">
                        {twin.communication_metrics.avg_pace_wpm ? `${Math.round(twin.communication_metrics.avg_pace_wpm)} WPM` : '135 WPM'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Speech Clarity:</span>
                      <span className="font-semibold text-cyan-400">
                        {Math.round((twin.communication_metrics.avg_clarity ?? 0.82) * 100)}%
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-slate-400">Filler Ratio:</span>
                      <span className="font-semibold text-slate-200">
                        {((twin.communication_metrics.avg_filler_ratio ?? 0.04) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-xs text-slate-500 flex items-center justify-between">
                  <span>Vocal Presence</span>
                  <button
                    onClick={() => handleExplain('communication')}
                    className="text-cyan-400 hover:text-cyan-300 font-medium underline-offset-2 hover:underline"
                  >
                    Explain &rarr;
                  </button>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex items-center gap-2 border-b border-slate-800">
              <button
                onClick={() => setActiveTab('overview')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                  activeTab === 'overview'
                    ? 'border-cyan-500 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Target className="w-4 h-4" />
                <span>Modal Competencies</span>
              </button>
              <button
                onClick={() => setActiveTab('calibration')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                  activeTab === 'calibration'
                    ? 'border-cyan-500 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <Layers className="w-4 h-4" />
                <span>DAG & SM-2 Calibration</span>
              </button>
              <button
                onClick={() => setActiveTab('trajectory')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                  activeTab === 'trajectory'
                    ? 'border-cyan-500 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <GitCommit className="w-4 h-4" />
                <span>Milestone Trajectory</span>
              </button>
              <button
                onClick={() => setActiveTab('benchmarks')}
                className={`px-4 py-2.5 text-sm font-medium border-b-2 transition flex items-center gap-2 ${
                  activeTab === 'benchmarks'
                    ? 'border-cyan-500 text-cyan-400'
                    : 'border-transparent text-slate-400 hover:text-slate-200'
                }`}
              >
                <BarChart2 className="w-4 h-4" />
                <span>Peer Benchmarking</span>
              </button>
            </div>

            {/* TAB 1: MODAL COMPETENCIES */}
            {activeTab === 'overview' && (
              <div className="space-y-8">
                {/* 5 Core Pillars Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  {/* 1. Technical Mastery */}
                  <div
                    onClick={() => handleExplain('technical')}
                    className="cursor-pointer group p-5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
                        <Cpu className="w-5 h-5" />
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                    <h4 className="mt-3 font-semibold text-slate-200 group-hover:text-white transition">
                      Technical Mastery
                    </h4>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-white">
                        {Math.round(twin.overall_readiness_score)}%
                      </span>
                      <span className="text-xs text-slate-500">synthesized</span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      Distributed consensus, API contracts, runtime complexity, and DB indexes.
                    </p>
                  </div>

                  {/* 2. System Design */}
                  <div
                    onClick={() => handleExplain('system_design')}
                    className="cursor-pointer group p-5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                        <Brain className="w-5 h-5" />
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                    <h4 className="mt-3 font-semibold text-slate-200 group-hover:text-white transition">
                      System Design
                    </h4>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-white">
                        {Math.round(twin.system_design_mastery?.overall_score ?? 75)}%
                      </span>
                      <span className="text-xs text-slate-500">
                        Disc: {Math.round((twin.system_design_mastery?.anti_buzzword_discipline ?? 0.95) * 100)}%
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      SPOF mitigation, capacity calculations, partitioning, and trade-off rigor.
                    </p>
                  </div>

                  {/* 3. Coding Execution */}
                  <div
                    onClick={() => handleExplain('coding')}
                    className="cursor-pointer group p-5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                        <Code2 className="w-5 h-5" />
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                    <h4 className="mt-3 font-semibold text-slate-200 group-hover:text-white transition">
                      Coding Rigor
                    </h4>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-white">
                        {Math.round(twin.coding_mastery?.overall_score ?? 85)}%
                      </span>
                      <span className="text-xs text-slate-500">
                        {twin.coding_mastery?.submissions_count ?? 1} subs
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      Sandboxed AST validation, cyclomatic complexity, and unit test pass rates.
                    </p>
                  </div>

                  {/* 4. Behavioral STAR */}
                  <div
                    onClick={() => handleExplain('behavioral')}
                    className="cursor-pointer group p-5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
                        <Users className="w-5 h-5" />
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                    <h4 className="mt-3 font-semibold text-slate-200 group-hover:text-white transition">
                      Behavioral STAR
                    </h4>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-white">
                        {Math.round(twin.behavioral_mastery?.overall_score ?? 78)}%
                      </span>
                      <span className="text-xs text-slate-500">
                        I/We: {(twin.behavioral_mastery?.i_we_ownership_ratio ?? 0.8).toFixed(1)}
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      Leadership principles, cross-functional ownership, and STAR+L structure.
                    </p>
                  </div>

                  {/* 5. SM-2 Spaced Retention */}
                  <div
                    onClick={() => handleExplain('sm2_retention')}
                    className="cursor-pointer group p-5 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-cyan-500/50 transition relative overflow-hidden"
                  >
                    <div className="flex items-start justify-between">
                      <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
                        <Zap className="w-5 h-5" />
                      </div>
                      <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-cyan-400 transition" />
                    </div>
                    <h4 className="mt-3 font-semibold text-slate-200 group-hover:text-white transition">
                      Memory Stability
                    </h4>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-2xl font-bold text-white">
                        {Math.round(sm2Stability.average_retention_pct)}%
                      </span>
                      <span className="text-xs text-slate-500">
                        {sm2Stability.total_cards} cards
                      </span>
                    </div>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">
                      SuperMemo-2 active recall stability and Ebbinghaus decay curve calibration.
                    </p>
                  </div>
                </div>

                {/* Strengths & Growth Areas Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Strong Areas */}
                  <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-semibold text-white flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                        Verified Strengths ({twin.strong_areas?.length ?? 0})
                      </h3>
                      <span className="text-xs text-slate-500">High Confidence Evidence</span>
                    </div>
                    {twin.strong_areas && twin.strong_areas.length > 0 ? (
                      <div className="space-y-3">
                        {twin.strong_areas.map((st, i) => (
                          <div
                            key={i}
                            className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                          >
                            <div>
                              <p className="text-sm font-medium text-slate-200 capitalize">{st.topic.replace('_', ' ')}</p>
                              <p className="text-xs text-slate-500">Confidence: {Math.round(st.confidence * 100)}%</p>
                            </div>
                            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/60">
                              {Math.round(st.score)}%
                            </span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic py-4">No verified strengths recorded yet.</p>
                    )}
                  </div>

                  {/* Weak Areas & Learning Plan Launcher */}
                  <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-semibold text-white flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        Growth Opportunities ({twin.weak_areas?.length ?? 0})
                      </h3>
                      <span className="text-xs text-slate-500">Targeted Remediation</span>
                    </div>
                    {twin.weak_areas && twin.weak_areas.length > 0 ? (
                      <div className="space-y-3">
                        {twin.weak_areas.map((wa, i) => (
                          <div
                            key={i}
                            className="p-3.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                          >
                            <div>
                              <p className="text-sm font-medium text-slate-200 capitalize">{wa.topic.replace('_', ' ')}</p>
                              <div className="flex items-center gap-2 mt-0.5">
                                <span
                                  className={`text-[10px] px-1.5 py-0.5 rounded uppercase font-bold ${
                                    wa.severity === 'high'
                                      ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                      : 'bg-amber-950 text-amber-300 border border-amber-800'
                                  }`}
                                >
                                  {wa.severity}
                                </span>
                                <span className="text-xs text-slate-500">{wa.evidence_turns} interview turns</span>
                              </div>
                            </div>
                            <Link
                              href={`/learning?focus=${encodeURIComponent(wa.topic)}`}
                              className="text-xs px-3 py-1.5 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 transition flex items-center gap-1"
                            >
                              Launch Plan
                              <ChevronRight className="w-3 h-3" />
                            </Link>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-500 italic py-4">No critical skill gaps currently detected.</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: DAG & SM-2 RETENTION CALIBRATION */}
            {activeTab === 'calibration' && (
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Skill DAG Calibration Card */}
                  <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Layers className="w-5 h-5 text-indigo-400" />
                        <h3 className="text-base font-semibold text-white">Skill Graph DAG Calibration</h3>
                      </div>
                      <Link
                        href="/skills"
                        className="text-xs text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                      >
                        Explore Taxonomy &rarr;
                      </Link>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <span className="text-xs text-slate-400">Verified Skills</span>
                        <div className="text-3xl font-bold text-white mt-1">
                          {dagCalibration.verified_skills_count}
                          <span className="text-sm font-normal text-slate-500"> / {dagCalibration.total_skills_evaluated || 1}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">Mastery score &ge; 70% threshold</p>
                      </div>

                      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <span className="text-xs text-slate-400">Highest Verified Tier</span>
                        <div className="text-3xl font-bold text-indigo-400 mt-1">
                          Tier {dagCalibration.highest_tier_verified}
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">Universal ontology depth</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-900/30 text-xs text-indigo-200">
                      <p className="font-semibold text-indigo-300 mb-1">Transitive Mastery Credit Propagation</p>
                      Your Twin continuously traverses prerequisite directed acyclic graphs to infer foundational credits with an 85% decay factor.
                    </div>
                  </div>

                  {/* SM-2 Spaced Repetition Card */}
                  <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Zap className="w-5 h-5 text-purple-400" />
                        <h3 className="text-base font-semibold text-white">SM-2 Spaced Memory Stability</h3>
                      </div>
                      <Link
                        href="/learning"
                        className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1"
                      >
                        Review Flashcards &rarr;
                      </Link>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <span className="text-xs text-slate-400">Average Retention</span>
                        <div className="text-3xl font-bold text-purple-400 mt-1">
                          {Math.round(sm2Stability.average_retention_pct)}%
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">Ebbinghaus forgetting curve</p>
                      </div>

                      <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                        <span className="text-xs text-slate-400">Mature Cards (&ge;21d)</span>
                        <div className="text-3xl font-bold text-white mt-1">
                          {sm2Stability.mature_cards_count}
                          <span className="text-sm font-normal text-slate-500"> / {sm2Stability.total_cards}</span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">Consolidated long-term recall</p>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-purple-950/20 border border-purple-900/30 text-xs text-purple-200">
                      <p className="font-semibold text-purple-300 mb-1">SuperMemo-2 Mathematical Recurrence</p>
                      Easiness Factors ($EF \ge 1.3$) and geometrical interval scheduling protect your conceptual knowledge against exponential forgetting.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: MILESTONE TRAJECTORY */}
            {activeTab === 'trajectory' && (
              <div className="space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-cyan-400" />
                    <div>
                      <h3 className="text-sm font-semibold text-white">Chronological Trajectory Timeline</h3>
                      <p className="text-xs text-slate-400">Interleaving interview sessions, code submissions, and SM-2 retention milestones.</p>
                    </div>
                  </div>

                  {/* Filter Pills */}
                  <div className="flex items-center gap-1.5 flex-wrap">
                    {[
                      { key: 'all', label: 'All Milestones' },
                      { key: 'interview_session', label: 'Interviews' },
                      { key: 'coding_submission', label: 'Coding' },
                      { key: 'sm2_retention', label: 'SM-2 Recall' },
                      { key: 'plan_completed', label: 'Plans' },
                    ].map((f) => (
                      <button
                        key={f.key}
                        onClick={() => handleFilterHistory(f.key)}
                        className={`text-xs px-3 py-1.5 rounded-lg border transition ${
                          historyFilter === f.key
                            ? 'bg-cyan-950 text-cyan-300 border-cyan-700 font-medium'
                            : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200'
                        }`}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>

                {historyEvents.length > 0 ? (
                  <div className="relative pl-6 border-l-2 border-slate-800 space-y-4">
                    {historyEvents.map((ev, idx) => (
                      <div key={idx} className="relative group">
                        {/* Bullet Marker */}
                        <div className="absolute -left-[31px] top-4 w-3.5 h-3.5 rounded-full bg-slate-900 border-2 border-cyan-400 group-hover:bg-cyan-400 transition" />

                        <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between hover:border-slate-700 transition">
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-slate-800 text-slate-300">
                                {ev.event_type.replace('_', ' ')}
                              </span>
                              <h4 className="text-sm font-medium text-slate-200">{ev.title}</h4>
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                              Recorded {new Date(ev.timestamp).toLocaleDateString()} at{' '}
                              {new Date(ev.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </p>
                          </div>

                          <div className="flex items-center gap-4 text-right">
                            <div>
                              <div className="text-base font-bold text-white">{Math.round(ev.score)}%</div>
                              <div
                                className={`text-xs font-semibold ${
                                  ev.delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                                }`}
                              >
                                {ev.delta >= 0 ? `+${ev.delta.toFixed(1)}` : ev.delta.toFixed(1)} pts
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-12 text-center rounded-xl bg-slate-900/40 border border-slate-800 text-slate-500">
                    No milestone events match this filter.
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: PEER BENCHMARKING */}
            {activeTab === 'benchmarks' && (
              <div className="space-y-6">
                {benchmarks ? (
                  <>
                    <div className="p-6 rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6">
                      <div>
                        <span className="text-xs uppercase tracking-wider text-indigo-400 font-semibold">
                          Cohort Comparison ({benchmarks.cohort_name})
                        </span>
                        <h3 className="text-2xl font-bold text-white mt-1">Peer Percentile Ranking</h3>
                        <p className="text-xs text-slate-400 mt-1">
                          Evaluated against enterprise engineer distributions normalized to Gaussian percentiles.
                        </p>
                      </div>

                      <div className="flex items-center gap-4 bg-slate-950/80 p-4 rounded-xl border border-slate-800">
                        <div className="text-center">
                          <span className="text-xs text-slate-500">Global Percentile</span>
                          <div className="text-4xl font-black text-indigo-400">
                            {Math.round(benchmarks.overall_percentile)}
                            <span className="text-lg font-light text-slate-500">th</span>
                          </div>
                        </div>
                        <div className="border-l border-slate-800 pl-4 text-xs space-y-1">
                          <div className="text-slate-400">
                            Velocity:{' '}
                            <span className={`font-semibold capitalize ${velocityStatusColor(benchmarks.growth_velocity_status)} px-1.5 py-0.2 rounded border`}>
                              {benchmarks.growth_velocity_status}
                            </span>
                          </div>
                          <div className="text-slate-400">
                            Cohort: <span className="text-slate-200">Senior L5 Cohort</span>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Metric Breakdowns */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {benchmarks.metrics.map((m, idx) => (
                        <div key={idx} className="p-5 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3">
                          <div className="flex items-center justify-between">
                            <h4 className="text-sm font-semibold text-slate-200">{m.metric}</h4>
                            <span className="text-xs font-bold px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                              {Math.round(m.percentile_rank)}th Percentile
                            </span>
                          </div>

                          <div className="flex items-baseline justify-between text-xs">
                            <span className="text-slate-400">
                              Candidate Score: <span className="font-bold text-white">{Math.round(m.candidate_score)}%</span>
                            </span>
                            <span className="text-slate-500">
                              Mean: {Math.round(m.cohort_mean)}% &bull; Top 25%: {Math.round(m.cohort_top_quartile)}%
                            </span>
                          </div>

                          <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-indigo-500 h-2 rounded-full"
                              style={{ width: `${Math.min(100, Math.max(0, m.percentile_rank))}%` }}
                            />
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div className="p-12 text-center text-slate-500 rounded-xl bg-slate-900/40 border border-slate-800">
                    Cohort benchmark data is still compiling.
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* Explainable AI Modal/Drawer (Feature 16) */}
        <AnimatePresence>
          {activeExplainDimension && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-2xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8 space-y-6 max-h-[90vh] overflow-y-auto"
              >
                <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-cyan-400">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Feature 16: Explainable AI Engine</span>
                    </div>
                    <h3 className="text-xl font-bold text-white mt-1 capitalize">
                      Score Rationale: {explainData?.dimension || activeExplainDimension.replace('_', ' ')}
                    </h3>
                  </div>
                  <button
                    onClick={closeExplain}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {explainLoading ? (
                  <div className="py-16 text-center text-slate-400 space-y-3">
                    <RefreshCw className="w-6 h-6 animate-spin text-cyan-400 mx-auto" />
                    <p className="text-sm">Synthesizing zero-hallucination explanation from raw telemetry...</p>
                  </div>
                ) : explainData ? (
                  <div className="space-y-6 text-sm">
                    {/* Score & Uplift Banner */}
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between">
                      <div>
                        <span className="text-xs text-slate-400">Calibrated Evaluation</span>
                        <p className="text-sm font-medium text-slate-200">{explainData.what_was_evaluated}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-3xl font-black text-cyan-400">
                          {Math.round(explainData.assigned_score)}%
                        </div>
                        {explainData.projected_score_uplift && explainData.projected_score_uplift > 0 && (
                          <span className="text-xs text-emerald-400 font-semibold">
                            +{explainData.projected_score_uplift} pts projected uplift
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Score Rationale */}
                    <div className="space-y-2">
                      <h4 className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                        Algorithmic Rationale
                      </h4>
                      <p className="text-slate-300 leading-relaxed bg-slate-950/40 p-4 rounded-xl border border-slate-800/80">
                        {explainData.score_rationale}
                      </p>
                    </div>

                    {/* Evidence Found */}
                    {explainData.evidence_found && explainData.evidence_found.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs uppercase tracking-wider text-emerald-400 font-semibold flex items-center gap-1.5">
                          <CheckCircle2 className="w-4 h-4" />
                          Verified Grounded Evidence
                        </h4>
                        <ul className="space-y-1.5 pl-4 list-disc text-slate-300 text-xs">
                          {explainData.evidence_found.map((ev, i) => (
                            <li key={i}>{ev}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* What is Missing */}
                    {explainData.what_is_missing && explainData.what_is_missing.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="text-xs uppercase tracking-wider text-amber-400 font-semibold flex items-center gap-1.5">
                          <AlertTriangle className="w-4 h-4" />
                          Limiting Factors & Active Blind Spots
                        </h4>
                        <ul className="space-y-1.5 pl-4 list-disc text-slate-300 text-xs">
                          {explainData.what_is_missing.map((ms, i) => (
                            <li key={i}>{ms}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Actionable Improvement Roadmap */}
                    {explainData.actionable_improvement_roadmap && explainData.actionable_improvement_roadmap.length > 0 && (
                      <div className="space-y-2 border-t border-slate-800 pt-4">
                        <h4 className="text-xs uppercase tracking-wider text-cyan-400 font-semibold flex items-center gap-1.5">
                          <Target className="w-4 h-4" />
                          Actionable 30-Day Uplift Roadmap
                        </h4>
                        <div className="space-y-2">
                          {explainData.actionable_improvement_roadmap.map((act, i) => (
                            <div
                              key={i}
                              className="p-3 rounded-lg bg-cyan-950/30 border border-cyan-800/40 text-cyan-200 text-xs flex items-start gap-2"
                            >
                              <span className="font-bold text-cyan-400">{i + 1}.</span>
                              <span>{act}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 py-6 text-center">No explanation data returned.</p>
                )}

                <div className="flex justify-end pt-4 border-t border-slate-800">
                  <button
                    onClick={closeExplain}
                    className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition"
                  >
                    Close Breakdown
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
