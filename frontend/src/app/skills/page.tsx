'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  GitFork,
  Network,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  BookOpen,
  Target,
  Compass,
  Cpu,
  Database,
  Server,
  Cloud,
  ShieldAlert,
  Flame,
  Award,
  RefreshCw,
  Zap,
} from 'lucide-react'
import { skillGraphApi } from '@/lib/api'
import type {
  SkillNode,
  SkillGraphDag,
  PathwayPlan,
  RootCauseGapReport,
  TransitiveCreditReport,
  RoleAlignmentReport,
  RoleArchetype,
} from '@/lib/types'

const TIER_LABELS: Record<number, { name: string; color: string; badge: string }> = {
  1: { name: 'Tier 1: Foundations', color: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-400', badge: 'Tier 1' },
  2: { name: 'Tier 2: Core Systems', color: 'border-blue-500/30 bg-blue-500/10 text-blue-400', badge: 'Tier 2' },
  3: { name: 'Tier 3: Applied Architecture', color: 'border-cyan-500/30 bg-cyan-500/10 text-cyan-400', badge: 'Tier 3' },
  4: { name: 'Tier 4: Distributed Infrastructure', color: 'border-purple-500/30 bg-purple-500/10 text-purple-400', badge: 'Tier 4' },
  5: { name: 'Tier 5: Staff / Principal Mastery', color: 'border-amber-500/30 bg-amber-500/10 text-amber-400', badge: 'Tier 5' },
}

export default function SkillGraphStudioPage() {
  const [activeTab, setActiveTab] = useState<'dag' | 'pathway' | 'root-cause' | 'transitive' | 'roles'>('dag')

  // DAG & Taxonomy Data
  const [dag, setDag] = useState<SkillGraphDag | null>(null)
  const [selectedNode, setSelectedNode] = useState<SkillNode | null>(null)
  const [selectedTierFilter, setSelectedTierFilter] = useState<number | 'all'>('all')
  const [selectedCategoryFilter, setSelectedCategoryFilter] = useState<string>('all')
  const [isLoadingDag, setIsLoadingDag] = useState<boolean>(true)

  // Pathway Generator State
  const [targetSkillId, setTargetSkillId] = useState<string>('raft_paxos_consensus')
  const [pathwayPlan, setPathwayPlan] = useState<PathwayPlan | null>(null)
  const [isGeneratingPathway, setIsGeneratingPathway] = useState<boolean>(false)

  // Root Cause State
  const [failedSkillsInput, setFailedSkillsInput] = useState<string[]>(['raft_paxos_consensus'])
  const [rootCauseReport, setRootCauseReport] = useState<RootCauseGapReport | null>(null)
  const [isDiagnosingGap, setIsDiagnosingGap] = useState<boolean>(false)

  // Transitive Credit State
  const [demonstratedSkillId, setDemonstratedSkillId] = useState<string>('raft_paxos_consensus')
  const [demonstratedScore, setDemonstratedScore] = useState<number>(92)
  const [decayFactor, setDecayFactor] = useState<number>(0.85)
  const [transitiveReport, setTransitiveReport] = useState<TransitiveCreditReport | null>(null)
  const [isPropagating, setIsPropagating] = useState<boolean>(false)

  // Role Archetypes State
  const [roles, setRoles] = useState<RoleArchetype[]>([])
  const [selectedRoleKey, setSelectedRoleKey] = useState<string>('senior_backend_l5')
  const [roleReport, setRoleReport] = useState<RoleAlignmentReport | null>(null)
  const [isEvaluatingRole, setIsEvaluatingRole] = useState<boolean>(false)

  // Load initial taxonomy & role archetypes
  useEffect(() => {
    async function loadTaxonomy() {
      try {
        setIsLoadingDag(true)
        const [dagData, rolesData] = await Promise.all([
          skillGraphApi.getDag(),
          skillGraphApi.getRoles(),
        ])
        setDag(dagData)
        setRoles(rolesData)
        if (dagData.nodes.length > 0) {
          setSelectedNode(dagData.nodes[0])
        }
      } catch (err) {
        console.error('Failed to load Skill Graph taxonomy', err)
      } finally {
        setIsLoadingDag(false)
      }
    }
    loadTaxonomy()
  }, [])

  // Action: Generate Pathway
  const handleGeneratePathway = async () => {
    try {
      setIsGeneratingPathway(true)
      const res = await skillGraphApi.getPathway(targetSkillId, {
        cs_fundamentals: 85,
        programming_basics: 80,
      })
      setPathwayPlan(res)
    } catch (err) {
      console.error('Pathway generation failed', err)
    } finally {
      setIsGeneratingPathway(false)
    }
  }

  // Action: Diagnose Root Causes
  const handleDiagnoseGaps = async () => {
    try {
      setIsDiagnosingGap(true)
      const res = await skillGraphApi.getRootCauseGaps(
        failedSkillsInput,
        {
          cs_fundamentals: 85,
          networking_tcp_ip: 80,
          os_fundamentals: 40, // Root deficiency
          multithreading_concurrency: 35,
        },
        65.0
      )
      setRootCauseReport(res)
    } catch (err) {
      console.error('Root cause gap analysis failed', err)
    } finally {
      setIsDiagnosingGap(false)
    }
  }

  // Action: Transitive Credit
  const handlePropagateTransitive = async () => {
    try {
      setIsPropagating(true)
      const res = await skillGraphApi.propagateTransitive(
        { [demonstratedSkillId]: demonstratedScore },
        decayFactor
      )
      setTransitiveReport(res)
    } catch (err) {
      console.error('Credit propagation failed', err)
    } finally {
      setIsPropagating(false)
    }
  }

  // Action: Evaluate Role Alignment
  const handleEvaluateRole = async (roleKey: string = selectedRoleKey) => {
    try {
      setIsEvaluatingRole(true)
      setSelectedRoleKey(roleKey)
      const res = await skillGraphApi.evaluateRoleAlignment(roleKey, {
        cs_fundamentals: 85,
        programming_basics: 82,
        data_structures_core: 80,
        relational_sql: 88,
        indexing_b_trees: 76,
        multithreading_concurrency: 78,
        http_rest_protocols: 84,
        containerization_docker: 75,
      })
      setRoleReport(res)
    } catch (err) {
      console.error('Role alignment evaluation failed', err)
    } finally {
      setIsEvaluatingRole(false)
    }
  }

  const filteredNodes = dag?.nodes.filter((n) => {
    const tierMatch = selectedTierFilter === 'all' || n.tier === selectedTierFilter
    const catMatch = selectedCategoryFilter === 'all' || n.category === selectedCategoryFilter
    return tierMatch && catMatch
  }) ?? []

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Header */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur px-6 py-4 sticky top-0 z-30 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link
            href="/dashboard"
            className="flex items-center space-x-2 text-slate-400 hover:text-white transition-colors"
          >
            <Compass className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold text-slate-300">InterviewAI</span>
          </Link>
          <span className="text-slate-600">/</span>
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-cyan-400" />
            <h1 className="text-lg font-bold text-white">Skill Graph & DAG Taxonomy</h1>
          </div>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-cyan-900/40 text-cyan-300 border border-cyan-800/60">
            Acyclic Directed Graph
          </span>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            26 Canonical Nodes
          </span>
          <span className="px-2.5 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-300 flex items-center gap-1.5">
            <GitFork className="w-3.5 h-3.5 text-purple-400" />
            39 Directed Edges
          </span>
          <span className="px-2.5 py-1 rounded-full bg-emerald-950/60 border border-emerald-800/60 text-emerald-400 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            0 Cycles (Strict DAG)
          </span>
        </div>
      </header>

      {/* Studio Sub-Navigation Tabs */}
      <div className="border-b border-slate-800/80 bg-slate-900/30 px-6 py-2.5 flex items-center space-x-3">
        <button
          onClick={() => setActiveTab('dag')}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'dag'
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Network className="w-4 h-4" />
          <span>DAG Taxonomy Explorer</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('pathway')
            if (!pathwayPlan) handleGeneratePathway()
          }}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'pathway'
              ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Compass className="w-4 h-4" />
          <span>Topological Pathway</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('root-cause')
            if (!rootCauseReport) handleDiagnoseGaps()
          }}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'root-cause'
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Root-Cause Diagnostic</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('transitive')
            if (!transitiveReport) handlePropagateTransitive()
          }}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'transitive'
              ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Zap className="w-4 h-4" />
          <span>Transitive Credit Decay</span>
        </button>

        <button
          onClick={() => {
            setActiveTab('roles')
            if (!roleReport) handleEvaluateRole('senior_backend_l5')
          }}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all ${
            activeTab === 'roles'
              ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40 shadow-sm'
              : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          <Award className="w-4 h-4" />
          <span>Role Archetype Alignment</span>
        </button>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-6 overflow-y-auto">
        {/* ── TAB 1: DAG TAXONOMY EXPLORER ───────────────────────────────────── */}
        {activeTab === 'dag' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left Filter & Node List (7 cols) */}
            <div className="lg:col-span-7 space-y-4">
              {/* Filter Bar */}
              <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex flex-wrap gap-4 items-center justify-between">
                <div className="flex flex-wrap gap-2 items-center">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tier:</span>
                  {(['all', 1, 2, 3, 4, 5] as const).map((t) => (
                    <button
                      key={t}
                      onClick={() => setSelectedTierFilter(t)}
                      className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                        selectedTierFilter === t
                          ? 'bg-cyan-500 text-slate-950 font-bold'
                          : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                      }`}
                    >
                      {t === 'all' ? 'All Tiers' : `T${t}`}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Category:</span>
                  <select
                    value={selectedCategoryFilter}
                    onChange={(e) => setSelectedCategoryFilter(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded px-2.5 py-1 outline-none focus:border-cyan-500"
                  >
                    <option value="all">All Categories</option>
                    {dag?.categories.map((c) => (
                      <option key={c} value={c}>
                        {c}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Node Cards */}
              <div className="space-y-3">
                {isLoadingDag ? (
                  <div className="p-12 text-center text-slate-500">Loading skill graph DAG...</div>
                ) : filteredNodes.length === 0 ? (
                  <div className="p-8 text-center text-slate-500">No skills match the current filters.</div>
                ) : (
                  filteredNodes.map((node) => {
                    const isSelected = selectedNode?.id === node.id
                    const tierMeta = TIER_LABELS[node.tier] ?? TIER_LABELS[1]

                    return (
                      <div
                        key={node.id}
                        onClick={() => setSelectedNode(node)}
                        className={`p-4 rounded-xl border transition-all cursor-pointer ${
                          isSelected
                            ? 'border-cyan-500 bg-cyan-950/20 shadow-md ring-1 ring-cyan-500/50'
                            : 'border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${tierMeta.color}`}>
                                {tierMeta.badge}
                              </span>
                              <span className="text-xs font-medium text-slate-400">{node.category}</span>
                            </div>
                            <h3 className="text-base font-semibold text-white">{node.name}</h3>
                          </div>
                          <ChevronRight
                            className={`w-5 h-5 transition-transform ${
                              isSelected ? 'text-cyan-400 rotate-90' : 'text-slate-600'
                            }`}
                          />
                        </div>

                        <p className="text-xs text-slate-400 line-clamp-2 mt-2">{node.description}</p>

                        <div className="flex items-center gap-4 mt-3 pt-3 border-t border-slate-800/60 text-[11px] text-slate-400">
                          <span className="flex items-center gap-1">
                            <span className="text-slate-500">Prereqs:</span>{' '}
                            <strong className="text-slate-300">{node.prerequisites.length}</strong>
                          </span>
                          <span className="flex items-center gap-1">
                            <span className="text-slate-500">Complements:</span>{' '}
                            <strong className="text-slate-300">{node.complements.length}</strong>
                          </span>
                        </div>
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Right Node Detail Inspector (5 cols) */}
            <div className="lg:col-span-5">
              <div className="sticky top-20 bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                {selectedNode ? (
                  <>
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span
                          className={`text-xs font-bold px-2.5 py-0.5 rounded border ${
                            TIER_LABELS[selectedNode.tier]?.color ?? ''
                          }`}
                        >
                          {TIER_LABELS[selectedNode.tier]?.name}
                        </span>
                        <span className="text-xs text-cyan-400 font-mono">ID: {selectedNode.id}</span>
                      </div>
                      <h2 className="text-xl font-bold text-white">{selectedNode.name}</h2>
                      <p className="text-sm text-slate-400 mt-2 leading-relaxed">
                        {selectedNode.description}
                      </p>
                    </div>

                    {/* Direct Prerequisites */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <ArrowRight className="w-3.5 h-3.5 text-purple-400 rotate-180" />
                        Direct Prerequisites ({selectedNode.prerequisites.length})
                      </h4>
                      {selectedNode.prerequisites.length === 0 ? (
                        <p className="text-xs text-emerald-400/80 italic">
                          Foundational entry point (No prerequisites required)
                        </p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {selectedNode.prerequisites.map((p) => {
                            const pNode = dag?.nodes.find((n) => n.id === p)
                            return (
                              <button
                                key={p}
                                onClick={() => pNode && setSelectedNode(pNode)}
                                className="px-2.5 py-1 rounded bg-purple-950/40 border border-purple-800/60 text-purple-300 text-xs hover:border-purple-500 transition-colors"
                              >
                                {pNode ? pNode.name : p}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>

                    {/* Complements & Specializations */}
                    <div>
                      <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                        Complements & Synergies ({selectedNode.complements.length})
                      </h4>
                      {selectedNode.complements.length === 0 ? (
                        <p className="text-xs text-slate-500 italic">None specified</p>
                      ) : (
                        <div className="flex flex-wrap gap-2">
                          {selectedNode.complements.map((c) => {
                            const cNode = dag?.nodes.find((n) => n.id === c)
                            return (
                              <button
                                key={c}
                                onClick={() => cNode && setSelectedNode(cNode)}
                                className="px-2.5 py-1 rounded bg-amber-950/40 border border-amber-800/60 text-amber-300 text-xs hover:border-amber-500 transition-colors"
                              >
                                {cNode ? cNode.name : c}
                              </button>
                            )
                          })}
                        </div>
                      )}
                    </div>

                    {/* Quick Pathway Action */}
                    <div className="pt-4 border-t border-slate-800 flex gap-2">
                      <button
                        onClick={() => {
                          setTargetSkillId(selectedNode.id)
                          setActiveTab('pathway')
                          handleGeneratePathway()
                        }}
                        className="flex-1 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <Compass className="w-3.5 h-3.5" />
                        Generate Learning Pathway
                      </button>
                      <button
                        onClick={() => {
                          setDemonstratedSkillId(selectedNode.id)
                          setActiveTab('transitive')
                          handlePropagateTransitive()
                        }}
                        className="py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center justify-center gap-1.5 transition-colors"
                      >
                        <Zap className="w-3.5 h-3.5 text-purple-400" />
                        Simulate Credit
                      </button>
                    </div>
                  </>
                ) : (
                  <p className="text-sm text-slate-500">Select a skill node on the left to inspect its edges.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── TAB 2: TOPOLOGICAL LEARNING PATHWAY ────────────────────────────── */}
        {activeTab === 'pathway' && (
          <div className="space-y-6 max-w-5xl mx-auto">
            {/* Target Skill Selector Bar */}
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Compass className="w-5 h-5 text-indigo-400" />
                    Topological Milestone Curriculum
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    Kahn&apos;s algorithm orders milestones so each foundational prerequisite is mastered before dependent concepts.
                  </p>
                </div>
                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <select
                    value={targetSkillId}
                    onChange={(e) => setTargetSkillId(e.target.value)}
                    className="bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-indigo-500"
                  >
                    {dag?.nodes.map((n) => (
                      <option key={n.id} value={n.id}>
                        [Tier {n.tier}] {n.name}
                      </option>
                    ))}
                  </select>
                  <button
                    onClick={handleGeneratePathway}
                    disabled={isGeneratingPathway}
                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors whitespace-nowrap"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isGeneratingPathway ? 'animate-spin' : ''}`} />
                    Calculate Path
                  </button>
                </div>
              </div>

              {pathwayPlan && (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs">
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400">Target Skill</span>
                    <p className="text-sm font-bold text-indigo-300 mt-0.5">{pathwayPlan.target_skill_name}</p>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400">Total Milestones</span>
                    <p className="text-sm font-bold text-white mt-0.5">{pathwayPlan.total_milestones} Steps</p>
                  </div>
                  <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80">
                    <span className="text-slate-400">Estimated Effort</span>
                    <p className="text-sm font-bold text-amber-400 mt-0.5">{pathwayPlan.estimated_total_hours} Hours Total</p>
                  </div>
                </div>
              )}
            </div>

            {/* Step-by-Step Curriculum Cards */}
            {pathwayPlan && (
              <div className="relative pl-6 space-y-4 before:absolute before:left-3 before:top-4 before:bottom-4 before:w-0.5 before:bg-indigo-500/30">
                {pathwayPlan.curriculum.map((m) => {
                  const isFinal = m.step === pathwayPlan.curriculum.length
                  return (
                    <div
                      key={m.step}
                      className={`relative p-5 rounded-xl border transition-all ${
                        isFinal
                          ? 'bg-indigo-950/30 border-indigo-500/50 shadow-md ring-1 ring-indigo-500/30'
                          : 'bg-slate-900 border-slate-800'
                      }`}
                    >
                      <div className="absolute -left-[30px] top-5 w-6 h-6 rounded-full bg-slate-900 border-2 border-indigo-500 flex items-center justify-center text-[10px] font-bold text-indigo-300">
                        {m.step}
                      </div>

                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                              Tier {m.tier}
                            </span>
                            <span className="text-xs text-indigo-400 font-medium">{m.category}</span>
                            {isFinal && (
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500 text-slate-950">
                                Target Objective
                              </span>
                            )}
                          </div>
                          <h4 className="text-base font-bold text-white mt-1">{m.name}</h4>
                        </div>
                        <div className="text-right text-xs">
                          <span className="text-slate-400">Study Time:</span>{' '}
                          <strong className="text-amber-400">{m.estimated_study_hours} hrs</strong>
                        </div>
                      </div>

                      <p className="text-xs text-slate-400 mt-2">{m.concept_summary}</p>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* ── TAB 3: ROOT-CAUSE PREREQUISITE DIAGNOSTIC ──────────────────────── */}
        {activeTab === 'root-cause' && (
          <div className="space-y-6 max-w-5xl mx-auto">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                    Root-Cause Prerequisite Gap Diagnostic
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    When high-tier assessments fail, DAG backtracking pinpoints whether the candidate lacks the complex skill itself or has an unmastered lower-tier prerequisite.
                  </p>
                </div>
                <button
                  onClick={handleDiagnoseGaps}
                  disabled={isDiagnosingGap}
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isDiagnosingGap ? 'animate-spin' : ''}`} />
                  Run Backtracking Analysis
                </button>
              </div>

              {/* Failed Skills Selector */}
              <div className="pt-3 border-t border-slate-800">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                  Select Simulated Failed Skills:
                </span>
                <div className="flex flex-wrap gap-2">
                  {['raft_paxos_consensus', 'distributed_transactions_2pc', 'lsm_trees_storage'].map((skillId) => {
                    const isSelected = failedSkillsInput.includes(skillId)
                    const node = dag?.nodes.find((n) => n.id === skillId)
                    return (
                      <button
                        key={skillId}
                        onClick={() => {
                          setFailedSkillsInput(
                            isSelected
                              ? failedSkillsInput.filter((s) => s !== skillId)
                              : [...failedSkillsInput, skillId]
                          )
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                          isSelected
                            ? 'bg-rose-950/60 border-rose-500 text-rose-300'
                            : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                        }`}
                      >
                        {node?.name ?? skillId}
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Root-Cause Results */}
            {rootCauseReport && (
              <div className="space-y-4">
                {rootCauseReport.root_causes.map((rc, idx) => (
                  <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                    <div className="flex items-start justify-between">
                      <div>
                        <span className="text-xs font-semibold text-rose-400 uppercase tracking-wider">
                          Failed Assessment
                        </span>
                        <h4 className="text-lg font-bold text-white mt-0.5">{rc.failed_skill_name}</h4>
                      </div>
                      <div className="px-3 py-1 rounded bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs font-bold">
                        Root: Tier {rc.root_cause_tier}
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-rose-950/20 border border-rose-900/40 text-xs text-rose-200">
                      <strong>Diagnostic Verdict:</strong> {rc.diagnosis}
                    </div>

                    <div>
                      <h5 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                        Topological Remedy Sequence:
                      </h5>
                      <div className="flex flex-wrap items-center gap-2">
                        {rc.remedy_sequence.map((step, sIdx) => (
                          <React.Fragment key={sIdx}>
                            <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium">
                              {step}
                            </span>
                            {sIdx < rc.remedy_sequence.length - 1 && (
                              <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── TAB 4: TRANSITIVE CREDIT DECAY ─────────────────────────────────── */}
        {activeTab === 'transitive' && (
          <div className="space-y-6 max-w-5xl mx-auto">
            <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-4">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-purple-400" />
                    Transitive Credit Propagation Simulator
                  </h3>
                  <p className="text-xs text-slate-400 mt-1">
                    When a candidate demonstrates high-tier mastery (e.g. Raft Consensus = 95%), credit automatically propagates backwards to ancestor prerequisites decayed by distance factor γ: Score = Base × γ^dist.
                  </p>
                </div>
                <button
                  onClick={handlePropagateTransitive}
                  disabled={isPropagating}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isPropagating ? 'animate-spin' : ''}`} />
                  Recalculate Propagation
                </button>
              </div>

              {/* Simulation Controls */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4 border-t border-slate-800 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Demonstrated Skill:</label>
                  <select
                    value={demonstratedSkillId}
                    onChange={(e) => setDemonstratedSkillId(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 outline-none focus:border-purple-500"
                  >
                    {dag?.nodes.filter((n) => n.tier >= 3).map((n) => (
                      <option key={n.id} value={n.id}>
                        [Tier {n.tier}] {n.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">
                    Direct Score: <strong className="text-white">{demonstratedScore}%</strong>
                  </label>
                  <input
                    type="range"
                    min="50"
                    max="100"
                    value={demonstratedScore}
                    onChange={(e) => setDemonstratedScore(Number(e.target.value))}
                    className="w-full accent-purple-500 mt-2"
                  />
                </div>

                <div>
                  <label className="text-slate-400 block mb-1">
                    Distance Decay Factor (γ): <strong className="text-white">{decayFactor}</strong>
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="0.95"
                    step="0.05"
                    value={decayFactor}
                    onChange={(e) => setDecayFactor(Number(e.target.value))}
                    className="w-full accent-purple-500 mt-2"
                  />
                </div>
              </div>
            </div>

            {/* Transitive Credit Grid */}
            {transitiveReport && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h4 className="text-sm font-bold text-white">
                    Propagation Output ({transitiveReport.total_skills_credited} Total Skills Credited)
                  </h4>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="text-emerald-400">1 Direct Assessment</span>
                    <span className="text-purple-400">
                      {transitiveReport.transitively_inferred_count} Transitively Inferred
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(transitiveReport.mastery_map).map(([sid, item]) => {
                    const node = dag?.nodes.find((n) => n.id === sid)
                    return (
                      <div
                        key={sid}
                        className={`p-3.5 rounded-lg border text-xs flex items-center justify-between ${
                          item.is_inferred
                            ? 'bg-purple-950/20 border-purple-800/40 text-slate-300'
                            : 'bg-emerald-950/30 border-emerald-500/50 text-white font-bold'
                        }`}
                      >
                        <div>
                          <div className="flex items-center gap-1.5 mb-0.5">
                            <span className="text-[10px] font-semibold px-1.5 py-0.2 rounded bg-slate-800 text-slate-300">
                              Tier {item.tier}
                            </span>
                            <span className="font-semibold text-white">{node?.name ?? sid}</span>
                          </div>
                          <span className="text-[10px] text-slate-500">
                            {item.is_inferred ? `Inferred (${Math.round(item.confidence * 100)}% conf)` : 'Direct Exam'}
                          </span>
                        </div>
                        <div className="text-right">
                          <span
                            className={`text-sm font-bold ${
                              item.is_inferred ? 'text-purple-300' : 'text-emerald-400'
                            }`}
                          >
                            {item.score}%
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TAB 5: ROLE ARCHETYPE BENCHMARK ALIGNMENT ───────────────────────── */}
        {activeTab === 'roles' && (
          <div className="space-y-6 max-w-5xl mx-auto">
            {/* Role Archetype Cards Bar */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {roles.map((r) => {
                const isSelected = selectedRoleKey === r.role_key
                return (
                  <div
                    key={r.role_key}
                    onClick={() => handleEvaluateRole(r.role_key)}
                    className={`p-5 rounded-xl border transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-amber-950/20 border-amber-500 ring-1 ring-amber-500/40'
                        : 'bg-slate-900 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span className="text-xs text-amber-400 font-semibold">{r.department}</span>
                    <h4 className="text-base font-bold text-white mt-1">{r.title}</h4>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-2">{r.description}</p>
                    <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-800 text-xs text-slate-400">
                      <span>{r.target_skills.length} Target Skills</span>
                      <span className="text-amber-400 font-bold">{r.passing_threshold}% Passing</span>
                    </div>
                  </div>
                )
              })}
            </div>

            {/* Alignment Evaluation Report */}
            {roleReport && (
              <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
                  <div>
                    <span className="text-xs text-slate-400 uppercase tracking-wider">Archetype Evaluation</span>
                    <h3 className="text-xl font-bold text-white mt-0.5">{roleReport.role_title}</h3>
                  </div>
                  <div className="flex items-center gap-4 text-center">
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Coverage</span>
                      <strong className="text-lg font-bold text-cyan-400">
                        {roleReport.coverage_percentage}%
                      </strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Readiness</span>
                      <strong className="text-lg font-bold text-amber-400">
                        {roleReport.composite_readiness}%
                      </strong>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-400 block uppercase">Verdict</span>
                      <span
                        className={`inline-block px-2.5 py-1 rounded text-xs font-bold ${
                          roleReport.verdict === 'Ready for Role'
                            ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                            : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                        }`}
                      >
                        {roleReport.verdict}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Verified vs Missing Skills Breakdown */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Verified Skills */}
                  <div>
                    <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Verified Skills ({roleReport.verified_skills_count})
                    </h4>
                    <div className="space-y-2">
                      {roleReport.verified_skills.length === 0 ? (
                        <p className="text-xs text-slate-500 italic">No skills verified yet</p>
                      ) : (
                        roleReport.verified_skills.map((s) => (
                          <div
                            key={s.skill_id}
                            className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-900/40 flex items-center justify-between text-xs"
                          >
                            <span className="text-white font-medium">{s.name}</span>
                            <span className="text-emerald-400 font-bold">{s.score}%</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Missing / Gap Skills */}
                  <div>
                    <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      Missing Skills & Target Deltas ({roleReport.missing_skills_count})
                    </h4>
                    <div className="space-y-2">
                      {roleReport.missing_skills.length === 0 ? (
                        <p className="text-xs text-emerald-400/80 italic">All archetype skills verified!</p>
                      ) : (
                        roleReport.missing_skills.map((s) => (
                          <div
                            key={s.skill_id}
                            className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/40 flex items-center justify-between text-xs"
                          >
                            <div>
                              <span className="text-white font-medium">{s.name}</span>
                              <span className="text-[10px] text-slate-500 block">Current: {s.score}%</span>
                            </div>
                            <span className="text-rose-400 font-bold">+{s.delta_needed}% needed</span>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>

                {/* Prioritized Learning Sequence */}
                {roleReport.prioritized_learning_sequence.length > 0 && (
                  <div className="pt-4 border-t border-slate-800">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                      Topologically Ordered Remediation Sequence:
                    </h4>
                    <div className="flex flex-wrap items-center gap-2">
                      {roleReport.prioritized_learning_sequence.map((step, sIdx) => (
                        <React.Fragment key={sIdx}>
                          <span className="px-2.5 py-1 rounded bg-slate-800 border border-slate-700 text-slate-200 text-xs font-medium">
                            {step}
                          </span>
                          {sIdx < roleReport.prioritized_learning_sequence.length - 1 && (
                            <ArrowRight className="w-3.5 h-3.5 text-slate-600" />
                          )}
                        </React.Fragment>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
