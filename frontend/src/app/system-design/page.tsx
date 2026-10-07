'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Layers,
  Cpu,
  ShieldAlert,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Database,
  Server,
  Network,
  Send,
  Sliders,
  Award,
  AlertCircle,
  HelpCircle,
  FileText,
  Boxes,
} from 'lucide-react'
import { systemDesignApi, interviewApi } from '@/lib/api'
import type {
  SystemDesignEvaluation,
  ArchitecturePillarScore,
  ValidateGraphResponse,
  CapacityEstimateResponse,
  ClarificationResponse,
} from '@/lib/types'

interface Scenario {
  key: string
  title: string
  domain: string
  prompt: string
  target_scale: string
  key_focus_areas: string[]
}

const PILLARS = [
  { id: 'requirements', name: '1. Requirements & Scope Clarification', placeholder: 'Clarify functional boundaries, user personas, read vs write workloads, traffic patterns...' },
  { id: 'non_functional', name: '2. Non-Functional Requirements & Capacity', placeholder: 'Throughput (QPS), p99 latency SLA (<2ms), storage volume per year, network bandwidth estimates...' },
  { id: 'high_level', name: '3. High-Level Component Topology', placeholder: 'Client -> CDN -> Edge Reverse Proxy / API Gateway -> Application Services -> Async Workers...' },
  { id: 'data_model', name: '4. Data Model, Schemas & Storage Engines', placeholder: 'Relational vs NoSQL choice, schema design, primary keys, indexing strategy, data lifecycle...' },
  { id: 'api_design', name: '5. API Contracts & Protocol Design', placeholder: 'REST / gRPC / WebSocket endpoints, payload schemas, idempotency tokens, error handling...' },
  { id: 'scalability', name: '6. Scalability, Partitioning & Caching Strategy', placeholder: 'Sharding keys, consistent hashing, caching layers (L1/L2 Redis), cache invalidation policies...' },
  { id: 'resilience', name: '7. Failure Modes, SPOF & Fault Tolerance', placeholder: 'Single points of failure, circuit breakers, dead letter queues, multi-region replication, failover...' },
  { id: 'trade_offs', name: '8. Core Architectural Trade-offs', placeholder: 'CAP theorem positioning, latency vs consistency, cost vs redundancy, technology justification...' },
]

export default function SystemDesignPage() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null)
  const [activeTab, setActiveTab] = useState<string>('requirements')
  const [sections, setSections] = useState<Record<string, string>>({
    requirements: '',
    non_functional: '',
    high_level: '',
    data_model: '',
    api_design: '',
    scalability: '',
    resilience: '',
    trade_offs: '',
  })

  const [loading, setLoading] = useState(true)
  const [evaluating, setEvaluating] = useState(false)
  const [evaluation, setEvaluation] = useState<SystemDesignEvaluation | null>(null)
  const [sessionId, setSessionId] = useState<string | null>(null)

  // Phase 11: Clarification, Capacity, and Graph Validation
  const [clarQuestion, setClarQuestion] = useState('')
  const [clarResponse, setClarResponse] = useState<ClarificationResponse | null>(null)
  const [askingClar, setAskingClar] = useState(false)

  const [readQps, setReadQps] = useState('')
  const [writeQps, setWriteQps] = useState('')
  const [dailyStorage, setDailyStorage] = useState('')
  const [bandwidth, setBandwidth] = useState('')
  const [ramCache, setRamCache] = useState('')
  const [capResult, setCapResult] = useState<CapacityEstimateResponse | null>(null)
  const [evaluatingCap, setEvaluatingCap] = useState(false)

  const [graphResult, setGraphResult] = useState<ValidateGraphResponse | null>(null)
  const [validatingGraph, setValidatingGraph] = useState(false)

  const handleAskClarification = async () => {
    if (!selectedScenario || !clarQuestion.trim()) return
    setAskingClar(true)
    try {
      const res = await systemDesignApi.askClarification({
        scenario_key: selectedScenario.key,
        question: clarQuestion,
      })
      setClarResponse(res)
    } catch (err) {
      console.error('Clarification failed:', err)
    } finally {
      setAskingClar(false)
    }
  }

  const handleVerifyCapacity = async () => {
    if (!selectedScenario) return
    setEvaluatingCap(true)
    try {
      const res = await systemDesignApi.estimateCapacity({
        scenario_key: selectedScenario.key,
        estimates: {
          read_qps: readQps ? parseFloat(readQps) : undefined,
          write_qps: writeQps ? parseFloat(writeQps) : undefined,
          daily_storage_gb: dailyStorage ? parseFloat(dailyStorage) : undefined,
          bandwidth_gbps: bandwidth ? parseFloat(bandwidth) : undefined,
          ram_cache_gb: ramCache ? parseFloat(ramCache) : undefined,
        },
      })
      setCapResult(res)
    } catch (err) {
      console.error('Capacity check failed:', err)
    } finally {
      setEvaluatingCap(false)
    }
  }

  const handleRunGraphValidation = async () => {
    setValidatingGraph(true)
    try {
      const components = [
        { id: 'cdn', name: 'CDN Edge', type: 'cdn', replicas: 50, is_clustered: true },
        { id: 'gw', name: 'API Gateway', type: 'gateway', replicas: 2, is_clustered: true },
        { id: 'app', name: 'Microservices Fleet', type: 'service', replicas: 6, is_clustered: true },
        { id: 'cache', name: 'Redis Cache', type: 'cache', replicas: 3, is_clustered: true },
        { id: 'db', name: 'Database Cluster', type: 'database', replicas: 2, is_clustered: true },
      ]
      const connections = [
        { from: 'cdn', to: 'gw' },
        { from: 'gw', to: 'app' },
        { from: 'app', to: 'cache' },
        { from: 'app', to: 'db' },
      ]
      const res = await systemDesignApi.validateGraph({ components, connections })
      setGraphResult(res)
    } catch (err) {
      console.error('Graph validation failed:', err)
    } finally {
      setValidatingGraph(false)
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        setLoading(true)
        const scList = await systemDesignApi.getScenarios()
        setScenarios(scList)
        if (scList.length > 0) {
          setSelectedScenario(scList[0])
        }

        // Initialize a lightweight session for audit & evaluation
        const sess = await interviewApi.createSession({
          target_question_count: 5,
          focus_categories: ['system_design'],
          adaptive_mode: false,
        })
        setSessionId(sess.id)
      } catch (err) {
        console.error('Failed to init system design scenarios:', err)
      } finally {
        setLoading(false)
      }
    }
    init()
  }, [])

  const handleScenarioChange = (key: string) => {
    const found = scenarios.find((s) => s.key === key)
    if (found) {
      setSelectedScenario(found)
      setEvaluation(null)
    }
  }

  const handleSectionChange = (pillarId: string, val: string) => {
    setSections((prev) => ({
      ...prev,
      [pillarId]: val,
    }))
  }

  const handleEvaluate = async () => {
    if (!selectedScenario || !sessionId) return
    try {
      setEvaluating(true)
      const res = await systemDesignApi.evaluate({
        session_id: sessionId,
        problem_title: selectedScenario.title,
        problem_prompt: selectedScenario.prompt,
        architecture_sections: sections,
      })
      setEvaluation(res)
    } catch (err: unknown) {
      console.error('Architecture evaluation failed:', err)
      alert(err instanceof Error ? err.message : 'Evaluation failed')
    } finally {
      setEvaluating(false)
    }
  }

  const getTierBadge = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'principal':
      case 'staff':
        return 'bg-purple-950 text-purple-300 border-purple-800'
      case 'senior':
        return 'bg-emerald-950 text-emerald-300 border-emerald-800'
      case 'mid-level':
        return 'bg-blue-950 text-blue-300 border-blue-800'
      default:
        return 'bg-amber-950 text-amber-300 border-amber-800'
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium mb-1">
              <Layers className="w-4 h-4" />
              <span>Feature 8: Specialized System Design Studio</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              8-Pillar Architectural Canvas & Evaluation
              <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-normal">
                Anti-Buzzword Evaluator
              </span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Structure enterprise distributed architectures with comprehensive SPOF analysis and rigorous technology trade-off grading.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <Link
              href="/behavioral"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-800 transition flex items-center gap-2"
            >
              <Award className="w-4 h-4" />
              STAR+L Behavioral
            </Link>
            <Link
              href="/coding"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-2"
            >
              <Cpu className="w-4 h-4" />
              Coding Studio
            </Link>
            <button
              onClick={handleEvaluate}
              disabled={evaluating || !selectedScenario}
              className="px-5 py-2 text-sm font-semibold rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-950 transition flex items-center gap-2 disabled:opacity-50"
            >
              {evaluating ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Grading 8 Pillars...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Evaluate Architecture</span>
                </>
              )}
            </button>
          </div>
        </div>

        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
            <p className="text-sm">Initializing architectural workspace...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Left Column: Problem Prompt & 8 Pillars Canvas */}
            <div className="space-y-6 lg:col-span-2">
              {/* Scenario Selector & Problem Statement */}
              <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <span className="text-xs uppercase tracking-wider text-cyan-400 font-semibold">
                      Enterprise Scenario Catalog
                    </span>
                    <h2 className="text-xl font-bold text-white mt-1">{selectedScenario?.title}</h2>
                  </div>
                  <select
                    value={selectedScenario?.key || ''}
                    onChange={(e) => handleScenarioChange(e.target.value)}
                    className="px-3.5 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs focus:outline-none focus:border-cyan-500"
                  >
                    {scenarios.map((s) => (
                      <option key={s.key} value={s.key}>
                        {s.title}
                      </option>
                    ))}
                  </select>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-4 rounded-xl border border-slate-800/80">
                  {selectedScenario?.prompt}
                </p>

                <div className="flex flex-wrap gap-4 text-xs pt-1">
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Boxes className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Domain: <strong className="text-slate-200">{selectedScenario?.domain}</strong></span>
                  </div>
                  <div className="flex items-center gap-1.5 text-slate-400">
                    <Server className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Target Scale: <strong className="text-slate-200">{selectedScenario?.target_scale}</strong></span>
                  </div>
                </div>
              </div>

              {/* Phase 11 Interactive Studio Tools: Clarification, Capacity Estimator, Graph SPOF Audit */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {/* Tool 1: Bar-Raiser Clarification */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-cyan-400 uppercase">
                    <HelpCircle className="w-4 h-4" />
                    <span>Bar-Raiser Clarification</span>
                  </div>
                  <input
                    type="text"
                    value={clarQuestion}
                    onChange={(e) => setClarQuestion(e.target.value)}
                    placeholder="Ask about consistency, QPS, latency SLAs..."
                    className="w-full text-xs px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-slate-200 focus:outline-none focus:border-cyan-500"
                  />
                  <button
                    onClick={handleAskClarification}
                    disabled={askingClar || !clarQuestion.trim()}
                    className="w-full py-1.5 rounded-lg bg-cyan-950 hover:bg-cyan-900 border border-cyan-800/80 text-cyan-300 text-xs font-semibold transition disabled:opacity-50"
                  >
                    {askingClar ? 'Consulting Bar-Raiser...' : 'Ask Clarification'}
                  </button>
                  {clarResponse && (
                    <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 space-y-1">
                      <p className="font-semibold text-white">Answer:</p>
                      <p className="text-slate-300 leading-relaxed">{clarResponse.answer}</p>
                    </div>
                  )}
                </div>

                {/* Tool 2: Capacity Math Estimator */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-emerald-400 uppercase">
                    <Sliders className="w-4 h-4" />
                    <span>Capacity Math Verifier</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <input
                      type="number"
                      value={readQps}
                      onChange={(e) => setReadQps(e.target.value)}
                      placeholder="Read QPS"
                      className="px-2.5 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-200 text-[11px]"
                    />
                    <input
                      type="number"
                      value={writeQps}
                      onChange={(e) => setWriteQps(e.target.value)}
                      placeholder="Write QPS"
                      className="px-2.5 py-1.5 rounded-md bg-slate-950 border border-slate-800 text-slate-200 text-[11px]"
                    />
                  </div>
                  <button
                    onClick={handleVerifyCapacity}
                    disabled={evaluatingCap}
                    className="w-full py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 border border-emerald-800/80 text-emerald-300 text-xs font-semibold transition disabled:opacity-50"
                  >
                    {evaluatingCap ? 'Verifying...' : 'Verify Math Accuracy'}
                  </button>
                  {capResult && (
                    <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 space-y-1">
                      <div className="flex items-center justify-between font-bold">
                        <span>Score: {capResult.overall_accuracy_score}%</span>
                        <span className="text-emerald-400">{capResult.rating}</span>
                      </div>
                      <p className="text-[10px] text-slate-400 italic line-clamp-2">{capResult.feedback[0]}</p>
                    </div>
                  )}
                </div>

                {/* Tool 3: Algorithmic SPOF Detector */}
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-3">
                  <div className="flex items-center gap-2 text-xs font-bold text-purple-400 uppercase">
                    <Network className="w-4 h-4" />
                    <span>Topology SPOF Audit</span>
                  </div>
                  <p className="text-[11px] text-slate-400">
                    Traverse component adjacency and detect single points of failure across ingress, cache, and database tiers.
                  </p>
                  <button
                    onClick={handleRunGraphValidation}
                    disabled={validatingGraph}
                    className="w-full py-1.5 rounded-lg bg-purple-950 hover:bg-purple-900 border border-purple-800/80 text-purple-300 text-xs font-semibold transition disabled:opacity-50"
                  >
                    {validatingGraph ? 'Auditing Graph...' : 'Run Topology Audit'}
                  </button>
                  {graphResult && (
                    <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-[11px] text-slate-300 space-y-1">
                      <div className="flex items-center justify-between font-bold">
                        <span>Status: {graphResult.is_resilient ? '✅ Resilient' : '⚠️ Vulnerable'}</span>
                        <span>{graphResult.resilience_score}/100</span>
                      </div>
                      <p className="text-[10px] text-slate-400">
                        {graphResult.spof_nodes.length === 0 ? 'No single point of failure found' : `${graphResult.spof_nodes.length} SPOFs flagged`}
                      </p>
                    </div>
                  )}
                </div>
              </div>

              {/* 8-Pillar Architectural Canvas Tabs */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                    Architectural Sections (8 Pillars)
                  </span>
                  <span className="text-[11px] text-slate-500">Provide concrete justifications</span>
                </div>

                {/* Pillar Horizontal Navigation */}
                <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/60 scrollbar-thin">
                  {PILLARS.map((p) => {
                    const isFilled = (sections[p.id] || '').trim().length > 0
                    const isActive = activeTab === p.id
                    return (
                      <button
                        key={p.id}
                        onClick={() => setActiveTab(p.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition flex items-center gap-1.5 ${
                          isActive
                            ? 'bg-cyan-950 text-cyan-300 border border-cyan-700'
                            : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 border border-slate-800'
                        }`}
                      >
                        {isFilled && <CheckCircle2 className="w-3 h-3 text-emerald-400" />}
                        <span>{p.name.split('.')[0]}</span>
                      </button>
                    )
                  })}
                </div>

                {/* Active Pillar Input Area */}
                {PILLARS.map((p) => {
                  if (activeTab !== p.id) return null
                  return (
                    <div key={p.id} className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-semibold text-white flex items-center gap-2">
                          <Network className="w-4 h-4 text-cyan-400" />
                          {p.name}
                        </h4>
                        <span className="text-[11px] text-slate-500">
                          {sections[p.id]?.length || 0} characters
                        </span>
                      </div>
                      <textarea
                        rows={12}
                        value={sections[p.id] || ''}
                        onChange={(e) => handleSectionChange(p.id, e.target.value)}
                        placeholder={p.placeholder}
                        className="w-full p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-white text-xs leading-relaxed placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono"
                      />
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Right Column: Real-Time Evaluation & Anti-Buzzword Radar */}
            <div className="space-y-6 lg:col-span-1">
              {evaluation ? (
                <div className="space-y-5">
                  {/* Overall Result Banner */}
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                          Evaluation Verdict
                        </span>
                        <div className="mt-1 flex items-baseline gap-2">
                          <span className="text-4xl font-black text-white">
                            {Math.round(evaluation.overall_score)}%
                          </span>
                          <span className="text-xs text-slate-500">Overall</span>
                        </div>
                      </div>
                      <span className={`text-xs px-2.5 py-1 rounded-full font-bold border ${getTierBadge(evaluation.tier)}`}>
                        {evaluation.tier} Tier
                      </span>
                    </div>

                    <p className="text-xs text-slate-300 bg-slate-950/60 p-3.5 rounded-xl border border-slate-800">
                      {evaluation.recommendation}
                    </p>
                  </div>

                  {/* Anti-Buzzword Discipline Card */}
                  <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                        Anti-Buzzword Analysis
                      </span>
                      <ShieldAlert className="w-4 h-4 text-amber-400" />
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Density Score</span>
                        <p className="font-bold text-white">
                          {Math.round(evaluation.buzzword_analysis.buzzword_density_score * 100)}%
                        </p>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-950 border border-slate-800">
                        <span className="text-[10px] text-slate-500">Penalty Applied</span>
                        <p className="font-bold text-rose-400">
                          -{Math.round(evaluation.buzzword_analysis.penalty_applied * 100)}%
                        </p>
                      </div>
                    </div>

                    {evaluation.buzzword_analysis.unjustified_buzzwords &&
                      evaluation.buzzword_analysis.unjustified_buzzwords.length > 0 && (
                        <div className="space-y-1.5 pt-2">
                          <span className="text-[10px] font-semibold uppercase text-rose-400">
                            Unjustified Technologies ({evaluation.buzzword_analysis.unjustified_buzzwords.length})
                          </span>
                          {evaluation.buzzword_analysis.unjustified_buzzwords.map((item, idx) => (
                            <div
                              key={idx}
                              className="p-2.5 rounded-lg bg-rose-950/30 border border-rose-800/40 text-[11px] space-y-0.5"
                            >
                              <span className="font-semibold text-rose-300">{item.buzzword}</span>
                              <p className="text-slate-400 text-[10px]">{item.advice}</p>
                            </div>
                          ))}
                        </div>
                      )}
                  </div>

                  {/* SPOF & Bottlenecks */}
                  <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                    <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                      Single Points of Failure ({evaluation.single_points_of_failure?.length ?? 0})
                    </span>
                    <ul className="space-y-1.5 pl-4 list-disc text-slate-300 text-xs">
                      {evaluation.single_points_of_failure?.map((spof, i) => (
                        <li key={i}>{spof}</li>
                      )) || <li className="text-slate-500 italic">No critical SPOFs flagged.</li>}
                    </ul>
                  </div>

                  {/* Pillar Scores Breakdown */}
                  <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
                    <span className="text-xs uppercase font-semibold text-slate-400 tracking-wider">
                      8-Pillar Scoring Detail
                    </span>
                    <div className="space-y-2">
                      {Object.entries(evaluation.pillar_scores).map(([k, p]: [string, ArchitecturePillarScore]) => (
                        <div
                          key={k}
                          className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-center justify-between text-xs"
                        >
                          <span className="text-slate-300 truncate max-w-[180px]">{p.pillar_name}</span>
                          <span className="font-mono font-bold text-cyan-400">
                            {Math.round(p.score * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800/80 text-center space-y-3">
                  <Cpu className="w-10 h-10 text-slate-600 mx-auto" />
                  <h4 className="text-sm font-medium text-slate-300">Ready for Evaluation</h4>
                  <p className="text-xs text-slate-500 leading-relaxed">
                    Fill out the architectural pillars on the left and click &quot;Evaluate Architecture&quot; to receive your comprehensive rubric grading and anti-buzzword audit.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
