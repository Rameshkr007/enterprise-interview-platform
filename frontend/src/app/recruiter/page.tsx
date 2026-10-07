'use client'

import React, { useEffect, useState } from 'react'
import {
  Users,
  Search,
  Sliders,
  FileText,
  TrendingUp,
  Award,
  CheckCircle2,
  AlertCircle,
  Clock,
  Sparkles,
  ArrowRight,
  Filter,
  Layers,
  ChevronDown,
  Edit3,
  Copy,
  Check,
  X,
  Plus,
  BarChart3,
  Target,
  ShieldCheck,
  Send,
} from 'lucide-react'
import { recruiterApi, enterpriseAnalyticsApi } from '@/lib/api'
import type {
  RecruiterRequisition,
  RequisitionCandidate,
  RequisitionCalibration,
  ExecutiveDebriefMemo,
  CandidateComparisonMatrix,
  TalentPoolMatch,
  EnterpriseOverview,
  RecruiterFunnelMetrics,
  CandidateStage,
  RequisitionUpdateRequest,
} from '@/lib/types'

const STAGE_LABELS: Record<CandidateStage, { label: string; color: string; bg: string }> = {
  invited: { label: 'Invited', color: 'text-sky-400', bg: 'bg-sky-500/10 border-sky-500/30' },
  in_progress: { label: 'In Progress', color: 'text-amber-400', bg: 'bg-amber-500/10 border-amber-500/30' },
  interviewed: { label: 'Interviewed', color: 'text-indigo-400', bg: 'bg-indigo-500/10 border-indigo-500/30' },
  review_required: { label: 'Review Required', color: 'text-purple-400', bg: 'bg-purple-500/10 border-purple-500/30' },
  offer: { label: 'Offer Extended', color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30' },
  rejected: { label: 'Archived', color: 'text-rose-400', bg: 'bg-rose-500/10 border-rose-500/30' },
}

export default function RecruiterCopilotPage() {
  const [requisitions, setRequisitions] = useState<RecruiterRequisition[]>([])
  const [selectedReq, setSelectedReq] = useState<RecruiterRequisition | null>(null)
  const [candidates, setCandidates] = useState<RequisitionCandidate[]>([])
  const [comparisonMatrix, setComparisonMatrix] = useState<CandidateComparisonMatrix | null>(null)
  const [calibrationData, setCalibrationData] = useState<RequisitionCalibration | null>(null)
  const [talentPool, setTalentPool] = useState<TalentPoolMatch[]>([])
  const [overview, setOverview] = useState<EnterpriseOverview | null>(null)
  const [funnel, setFunnel] = useState<RecruiterFunnelMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'pipeline' | 'calibration' | 'comparison' | 'talent' | 'analytics'>('pipeline')

  // Modals & Drawers
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditWeightsModal, setShowEditWeightsModal] = useState(false)
  const [showDebriefMemoModal, setShowDebriefMemoModal] = useState(false)
  const [showStageUpdateModal, setShowStageUpdateModal] = useState(false)
  const [activeMemo, setActiveMemo] = useState<ExecutiveDebriefMemo | null>(null)
  const [memoLoading, setMemoLoading] = useState(false)
  const [memoCopied, setMemoCopied] = useState(false)

  // Stage update state
  const [stageCandidate, setStageCandidate] = useState<RequisitionCandidate | null>(null)
  const [newStage, setNewStage] = useState<CandidateStage>('interviewed')
  const [recruiterNote, setRecruiterNote] = useState('')

  // New Requisition Form State
  const [newTitle, setNewTitle] = useState('')
  const [newDept, setNewDept] = useState('Engineering')
  const [newSkills, setNewSkills] = useState('distributed-systems, python, system_design, kafka')
  const [newThreshold, setNewThreshold] = useState(75)

  // Weight edit form state
  const [weightsTech, setWeightsTech] = useState(30)
  const [weightsSd, setWeightsSd] = useState(25)
  const [weightsCode, setWeightsCode] = useState(25)
  const [weightsBehav, setWeightsBehav] = useState(20)
  const [editThreshold, setEditThreshold] = useState(75)

  // Stage filter for pipeline
  const [stageFilter, setStageFilter] = useState<string>('all')

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    if (selectedReq) {
      loadRequisitionData(selectedReq.id)
      setWeightsTech(Math.round((selectedReq.rubric_weights?.technical ?? 0.3) * 100))
      setWeightsSd(Math.round((selectedReq.rubric_weights?.system_design ?? 0.25) * 100))
      setWeightsCode(Math.round((selectedReq.rubric_weights?.coding ?? 0.25) * 100))
      setWeightsBehav(Math.round((selectedReq.rubric_weights?.behavioral ?? 0.2) * 100))
      setEditThreshold(Math.round(selectedReq.hiring_threshold))
    }
  }, [selectedReq?.id])

  async function loadData() {
    setLoading(true)
    try {
      const [reqs, ov, fn] = await Promise.allSettled([
        recruiterApi.getRequisitions(),
        enterpriseAnalyticsApi.getOverview(),
        enterpriseAnalyticsApi.getFunnel(),
      ])

      if (reqs.status === 'fulfilled') {
        setRequisitions(reqs.value)
        if (reqs.value.length > 0) {
          setSelectedReq(reqs.value[0])
        }
      }
      if (ov.status === 'fulfilled') setOverview(ov.value)
      if (fn.status === 'fulfilled') setFunnel(fn.value)
    } finally {
      setLoading(false)
    }
  }

  async function loadRequisitionData(reqId: string) {
    try {
      const [cands, matrix, calib] = await Promise.allSettled([
        recruiterApi.getCandidates(reqId),
        recruiterApi.compareCandidates(reqId),
        recruiterApi.getCalibration(reqId),
      ])

      if (cands.status === 'fulfilled') setCandidates(cands.value)
      if (matrix.status === 'fulfilled') setComparisonMatrix(matrix.value)
      if (calib.status === 'fulfilled') setCalibrationData(calib.value)
    } catch {
      // non-fatal
    }
  }

  async function handleSearchTalent() {
    try {
      const matches = await recruiterApi.searchTalentPool(65)
      setTalentPool(matches)
    } catch {
      setTalentPool([])
    }
  }

  async function handleCreateRequisition(e: React.FormEvent) {
    e.preventDefault()
    if (!newTitle.trim()) return
    const skills = newSkills.split(',').map((s) => s.trim()).filter(Boolean)
    try {
      const created = await recruiterApi.createRequisition({
        title: newTitle,
        department: newDept,
        required_skills: skills,
        hiring_threshold: newThreshold,
      })
      setRequisitions([created, ...requisitions])
      setSelectedReq(created)
      setShowCreateModal(false)
      setNewTitle('')
    } catch {
      alert('Failed to create requisition')
    }
  }

  async function handleSaveWeights(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedReq) return
    const total = weightsTech + weightsSd + weightsCode + weightsBehav
    if (total !== 100) {
      alert(`Rubric weights must sum to 100%. Current sum: ${total}%`)
      return
    }

    const payload: RequisitionUpdateRequest = {
      rubric_weights: {
        technical: weightsTech / 100,
        system_design: weightsSd / 100,
        coding: weightsCode / 100,
        behavioral: weightsBehav / 100,
      },
      hiring_threshold: editThreshold,
    }

    try {
      const updated = await recruiterApi.updateRequisition(selectedReq.id, payload)
      setSelectedReq(updated)
      setRequisitions((prev) => prev.map((r) => (r.id === updated.id ? updated : r)))
      setShowEditWeightsModal(false)
      loadRequisitionData(updated.id)
    } catch {
      alert('Failed to update requisition settings')
    }
  }

  async function handleEvaluateCandidate(candidateId: string) {
    if (!selectedReq) return
    try {
      await recruiterApi.evaluateCandidate(selectedReq.id, candidateId)
      await loadRequisitionData(selectedReq.id)
    } catch {
      alert('Evaluation failed. Please verify candidate data.')
    }
  }

  async function handleOpenDebriefMemo(candidateId: string) {
    if (!selectedReq) return
    setMemoLoading(true)
    setShowDebriefMemoModal(true)
    try {
      const memo = await recruiterApi.getDebriefMemo(selectedReq.id, candidateId)
      setActiveMemo(memo)
    } catch {
      alert('Failed to generate debrief memo')
      setShowDebriefMemoModal(false)
    } finally {
      setMemoLoading(false)
    }
  }

  async function handleUpdateStageSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!selectedReq || !stageCandidate) return
    try {
      await recruiterApi.updateCandidateStage(selectedReq.id, stageCandidate.candidate_id, {
        stage: newStage,
        recruiter_notes: recruiterNote.trim() || undefined,
      })
      setShowStageUpdateModal(false)
      setRecruiterNote('')
      await loadRequisitionData(selectedReq.id)
    } catch {
      alert('Failed to update candidate stage')
    }
  }

  async function handleApplyThreshold(thresholdVal: number) {
    if (!selectedReq) return
    try {
      const updated = await recruiterApi.updateRequisition(selectedReq.id, {
        hiring_threshold: thresholdVal,
      })
      setSelectedReq(updated)
      setEditThreshold(thresholdVal)
      await loadRequisitionData(selectedReq.id)
    } catch {
      alert('Failed to apply threshold')
    }
  }

  const filteredCandidates = candidates.filter((c) =>
    stageFilter === 'all' ? true : c.status === stageFilter
  )

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 p-6 md:p-10 font-sans">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-8 border-b border-slate-800 gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="h-12 w-12 rounded-2xl bg-indigo-600/20 border border-indigo-500/40 flex items-center justify-center text-indigo-400 font-bold text-xl shadow-lg shadow-indigo-600/10">
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl md:text-3xl font-bold tracking-tight">Recruiter Copilot & Studio</h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Phase 15
                </span>
              </div>
              <p className="text-sm text-slate-400 mt-0.5">
                Multi-dimensional candidate evaluation, Bar-Raiser hiring debriefs & dynamic requisition calibration
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              handleSearchTalent()
              setActiveTab('talent')
            }}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition"
          >
            <Search className="w-4 h-4 text-slate-400" />
            Search Talent Pool
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 transition"
          >
            <Plus className="w-4 h-4" />
            New Requisition
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-4 my-6 border-b border-slate-800">
        {(['pipeline', 'calibration', 'comparison', 'talent', 'analytics'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-3 text-sm font-semibold capitalize transition relative flex items-center gap-2 ${
              activeTab === tab ? 'text-indigo-400 border-b-2 border-indigo-500' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab === 'pipeline' && (
              <>
                <Users className="w-4 h-4" />
                Candidate Pipeline
                {candidates.length > 0 && (
                  <span className="ml-1 px-1.5 py-0.5 text-[10px] rounded-full bg-slate-800 text-slate-300">
                    {candidates.length}
                  </span>
                )}
              </>
            )}
            {tab === 'calibration' && (
              <>
                <Sliders className="w-4 h-4" />
                Calibration Studio
              </>
            )}
            {tab === 'comparison' && (
              <>
                <Layers className="w-4 h-4" />
                Decision Matrix
              </>
            )}
            {tab === 'talent' && (
              <>
                <Target className="w-4 h-4" />
                Talent Pool
              </>
            )}
            {tab === 'analytics' && (
              <>
                <BarChart3 className="w-4 h-4" />
                Funnel Analytics
              </>
            )}
          </button>
        ))}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="flex justify-center items-center py-24 text-slate-400 gap-3">
          <Clock className="w-5 h-5 animate-spin text-indigo-400" />
          <span>Loading recruiter studio...</span>
        </div>
      ) : (
        <>
          {/* TAB 1: PIPELINE */}
          {activeTab === 'pipeline' && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Requisitions Sidebar */}
              <div className="lg:col-span-1 space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Requisitions</h3>
                  <span className="text-xs text-indigo-400">{requisitions.length} Open</span>
                </div>
                {requisitions.length === 0 ? (
                  <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-400">
                    No requisitions found. Click &quot;+ New Requisition&quot; to begin.
                  </div>
                ) : (
                  <div className="space-y-2">
                    {requisitions.map((req) => (
                      <div
                        key={req.id}
                        onClick={() => setSelectedReq(req)}
                        className={`p-4 rounded-xl border cursor-pointer transition ${
                          selectedReq?.id === req.id
                            ? 'bg-indigo-950/40 border-indigo-500/50 text-indigo-100 shadow-md shadow-indigo-950/40'
                            : 'bg-slate-900 border-slate-800 hover:border-slate-700 text-slate-300'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="font-semibold text-sm line-clamp-1">{req.title}</div>
                          <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                            {req.seniority_level}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 mt-2 flex justify-between">
                          <span>{req.department}</span>
                          <span className="font-medium text-indigo-300">Cutoff: {req.hiring_threshold}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Candidates Grid */}
              <div className="lg:col-span-3">
                {selectedReq ? (
                  <div className="space-y-5">
                    {/* Requisition Banner */}
                    <div className="p-5 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col md:flex-row justify-between md:items-center gap-4">
                      <div>
                        <div className="flex items-center gap-3">
                          <h2 className="text-xl font-bold text-white">{selectedReq.title}</h2>
                          <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                            {selectedReq.status.toUpperCase()}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                          {selectedReq.required_skills.map((s, idx) => (
                            <span key={idx} className="px-2.5 py-0.5 rounded-md bg-slate-800 text-xs text-slate-300 border border-slate-700/50">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className="text-xs text-slate-400">Hiring Cutoff</div>
                          <div className="text-lg font-bold text-indigo-400">{selectedReq.hiring_threshold}%</div>
                        </div>
                        <button
                          onClick={() => setShowEditWeightsModal(true)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition"
                        >
                          <Edit3 className="w-3.5 h-3.5" />
                          Calibrate Rubric
                        </button>
                      </div>
                    </div>

                    {/* Stage Filter Buttons */}
                    <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
                      <span className="text-slate-500 font-medium mr-1 flex items-center gap-1">
                        <Filter className="w-3.5 h-3.5" /> Stage:
                      </span>
                      {['all', 'invited', 'in_progress', 'interviewed', 'review_required', 'offer', 'rejected'].map((st) => (
                        <button
                          key={st}
                          onClick={() => setStageFilter(st)}
                          className={`px-3 py-1 rounded-lg font-medium transition capitalize whitespace-nowrap ${
                            stageFilter === st
                              ? 'bg-indigo-600 text-white'
                              : 'bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          {st.replace('_', ' ')}
                        </button>
                      ))}
                    </div>

                    {/* Candidate Cards Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {filteredCandidates.length > 0 ? (
                        filteredCandidates.map((c) => {
                          const stageInfo = STAGE_LABELS[c.status] || STAGE_LABELS.invited
                          return (
                            <div
                              key={c.id}
                              className="p-5 bg-slate-900/90 border border-slate-800 rounded-2xl space-y-4 hover:border-slate-700 transition shadow-sm"
                            >
                              <div className="flex justify-between items-start">
                                <div>
                                  <h4 className="font-semibold text-base text-slate-100">
                                    Candidate #{c.candidate_id.slice(0, 8)}
                                  </h4>
                                  <span className={`inline-block mt-1 px-2.5 py-0.5 text-xs font-semibold rounded-full border ${stageInfo.bg} ${stageInfo.color}`}>
                                    {stageInfo.label}
                                  </span>
                                </div>
                                <span
                                  className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${
                                    c.hiring_recommendation === 'Hire' || c.hiring_recommendation === 'Strong Hire'
                                      ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                      : c.hiring_recommendation === 'Lean Hire'
                                      ? 'bg-sky-500/20 text-sky-400 border-sky-500/30'
                                      : c.hiring_recommendation
                                      ? 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                                      : 'bg-slate-800 text-slate-400 border-slate-700'
                                  }`}
                                >
                                  {c.hiring_recommendation || 'Under Review'}
                                </span>
                              </div>

                              {/* Telemetry Metrics */}
                              <div className="grid grid-cols-3 gap-2 py-3 border-y border-slate-800/80 text-center bg-slate-950/40 rounded-xl">
                                <div>
                                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Composite</span>
                                  <div className="text-base font-extrabold text-indigo-400">
                                    {c.composite_score !== null && c.composite_score !== undefined
                                      ? `${c.composite_score.toFixed(1)}%`
                                      : '—'}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Skill Match</span>
                                  <div className="text-base font-extrabold text-emerald-400">
                                    {c.evidence_summary?.skill_match_percentage !== undefined
                                      ? `${c.evidence_summary.skill_match_percentage.toFixed(0)}%`
                                      : '—'}
                                  </div>
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 uppercase tracking-wider">Growth Velocity</span>
                                  <div className="text-base font-extrabold text-blue-400">
                                    {c.evidence_summary?.growth_velocity !== undefined
                                      ? `${c.evidence_summary.growth_velocity > 0 ? '+' : ''}${c.evidence_summary.growth_velocity.toFixed(2)}`
                                      : '—'}
                                  </div>
                                </div>
                              </div>

                              {/* Verified skills */}
                              {c.evidence_summary?.verified_skills && (
                                <div className="text-xs text-slate-400">
                                  <span className="font-semibold text-slate-300">Verified:</span>{' '}
                                  {c.evidence_summary.verified_skills.join(', ') || 'Evaluating multi-modal evidence'}
                                </div>
                              )}

                              {/* Recruiter Notes snippet */}
                              {c.recruiter_notes && (
                                <div className="p-2.5 bg-slate-950/70 border border-slate-800 rounded-lg text-xs text-slate-300 line-clamp-2">
                                  <span className="text-slate-500 font-semibold">Notes:</span> {c.recruiter_notes}
                                </div>
                              )}

                              {/* Action Buttons */}
                              <div className="flex items-center gap-2 pt-1">
                                <button
                                  onClick={() => handleEvaluateCandidate(c.candidate_id)}
                                  className="flex-1 py-1.5 px-3 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-lg border border-slate-700 transition flex items-center justify-center gap-1.5"
                                >
                                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                                  Run AI Copilot
                                </button>
                                <button
                                  onClick={() => handleOpenDebriefMemo(c.candidate_id)}
                                  className="flex-1 py-1.5 px-3 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold rounded-lg border border-indigo-500/30 transition flex items-center justify-center gap-1.5"
                                >
                                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                                  Debrief Memo
                                </button>
                                <button
                                  onClick={() => {
                                    setStageCandidate(c)
                                    setNewStage(c.status)
                                    setShowStageUpdateModal(true)
                                  }}
                                  className="py-1.5 px-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-lg border border-slate-700 transition"
                                  title="Advance Stage"
                                >
                                  <ArrowRight className="w-4 h-4" />
                                </button>
                              </div>
                            </div>
                          )
                        })
                      ) : (
                        <div className="col-span-2 p-12 text-center bg-slate-900/50 border border-slate-800 rounded-2xl text-slate-400 space-y-2">
                          <Users className="w-8 h-8 text-slate-600 mx-auto" />
                          <div>No candidates found matching this stage filter.</div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="p-12 text-center text-slate-400">Select a requisition to view its candidate pipeline.</div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: CALIBRATION STUDIO */}
          {activeTab === 'calibration' && selectedReq && (
            <div className="space-y-6">
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Sliders className="w-5 h-5 text-indigo-400" />
                    Requisition Calibration & What-If Studio
                  </h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Calibrate rubric thresholds against candidate cohort distributions and statistical percentiles.
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-xs text-slate-400">Current Threshold:</div>
                  <span className="text-lg font-bold text-indigo-400 px-3 py-1 rounded-xl bg-slate-950 border border-slate-800">
                    {selectedReq.hiring_threshold}%
                  </span>
                </div>
              </div>

              {calibrationData ? (
                <>
                  {/* Percentiles Summary Cards */}
                  <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Mean Score</div>
                      <div className="text-xl font-extrabold text-white mt-1">{calibrationData.percentiles.mean}%</div>
                    </div>
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Median (P50)</div>
                      <div className="text-xl font-extrabold text-white mt-1">{calibrationData.percentiles.median}%</div>
                    </div>
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-indigo-400">75th Percentile</div>
                      <div className="text-xl font-extrabold text-indigo-400 mt-1">{calibrationData.percentiles.p75}%</div>
                    </div>
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-purple-400">90th Percentile</div>
                      <div className="text-xl font-extrabold text-purple-400 mt-1">{calibrationData.percentiles.p90}%</div>
                    </div>
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-emerald-400">Qualify Rate</div>
                      <div className="text-xl font-extrabold text-emerald-400 mt-1">
                        {calibrationData.qualification_rate_pct}%
                      </div>
                    </div>
                    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl text-center">
                      <div className="text-[10px] uppercase font-bold text-slate-400">Cohort Size</div>
                      <div className="text-xl font-extrabold text-slate-200 mt-1">{calibrationData.sample_size}</div>
                    </div>
                  </div>

                  {/* Sensitivity Curve Table & Simulator */}
                  <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <h4 className="font-bold text-base text-white">Threshold Sensitivity Analysis (What-If)</h4>
                        <p className="text-xs text-slate-400">
                          Inspect cohort qualification volume across hypothetical hiring cutoffs.
                        </p>
                      </div>
                    </div>

                    <div className="space-y-3 pt-2">
                      {calibrationData.sensitivity_curve.map((row) => {
                        const isCurrent = row.threshold === selectedReq.hiring_threshold
                        return (
                          <div
                            key={row.threshold}
                            className={`p-3.5 rounded-xl border flex items-center justify-between gap-4 transition ${
                              isCurrent
                                ? 'bg-indigo-950/40 border-indigo-500/50'
                                : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                            }`}
                          >
                            <div className="w-32 flex items-center gap-2">
                              <span className="font-bold text-sm text-slate-200">{row.threshold}% Cutoff</span>
                              {isCurrent && (
                                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-500/30 text-indigo-300">
                                  Active
                                </span>
                              )}
                            </div>

                            <div className="flex-1 bg-slate-800 rounded-full h-3 overflow-hidden">
                              <div
                                className={`h-full rounded-full transition-all ${
                                  isCurrent ? 'bg-indigo-500' : 'bg-slate-600'
                                }`}
                                style={{ width: `${Math.min(row.qualification_rate_pct, 100)}%` }}
                              />
                            </div>

                            <div className="w-24 text-right">
                              <span className="font-bold text-sm text-slate-200">{row.qualification_rate_pct}%</span>
                              <span className="text-xs text-slate-500 ml-1">({row.qualified_count} cands)</span>
                            </div>

                            <button
                              disabled={isCurrent}
                              onClick={() => handleApplyThreshold(row.threshold)}
                              className={`px-3 py-1 text-xs font-semibold rounded-lg transition ${
                                isCurrent
                                  ? 'bg-slate-800 text-slate-500 cursor-default'
                                  : 'bg-indigo-600 hover:bg-indigo-500 text-white'
                              }`}
                            >
                              Apply
                            </button>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                </>
              ) : (
                <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-2xl text-slate-400">
                  Loading calibration analytics...
                </div>
              )}
            </div>
          )}

          {/* TAB 3: COMPARISON MATRIX */}
          {activeTab === 'comparison' && (
            <div className="space-y-6">
              {comparisonMatrix && comparisonMatrix.matrix.length > 0 ? (
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-bold text-white">Comparative Decision Matrix</h3>
                      <p className="text-xs text-slate-400">
                        {comparisonMatrix.total_compared} candidates evaluated against identical weighted rubrics.
                      </p>
                    </div>
                    {comparisonMatrix.top_candidate_id && (
                      <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-semibold">
                        <Award className="w-4 h-4 text-amber-400" />
                        Top Rank: #{comparisonMatrix.top_candidate_id.slice(0, 8)}
                      </div>
                    )}
                  </div>

                  <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/80">
                    <table className="w-full text-left border-collapse text-sm">
                      <thead>
                        <tr className="border-b border-slate-800 bg-slate-900 text-xs text-slate-400 uppercase tracking-wider">
                          <th className="p-4">Candidate</th>
                          <th className="p-4">Composite Score</th>
                          <th className="p-4">Recommendation</th>
                          <th className="p-4">Technical (30%)</th>
                          <th className="p-4">Coding (25%)</th>
                          <th className="p-4">System Design (25%)</th>
                          <th className="p-4">Behavioral (20%)</th>
                          <th className="p-4">Communication</th>
                          <th className="p-4">Velocity</th>
                          <th className="p-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800">
                        {comparisonMatrix.matrix.map((c, idx) => (
                          <tr key={c.candidate_id} className="hover:bg-slate-800/40 transition">
                            <td className="p-4 font-semibold text-slate-200">
                              <div className="flex items-center gap-2">
                                {idx === 0 && <Award className="w-4 h-4 text-amber-400" />}
                                <span>{c.full_name}</span>
                              </div>
                              <div className="text-xs text-slate-400 font-normal">{c.email}</div>
                            </td>
                            <td className="p-4 font-extrabold text-indigo-400 text-base">
                              {c.composite_score?.toFixed(1) ?? 'N/A'}%
                            </td>
                            <td className="p-4">
                              <span
                                className={`px-2.5 py-1 text-xs font-bold rounded-lg border ${
                                  c.hiring_recommendation === 'Hire' || c.hiring_recommendation === 'Strong Hire'
                                    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                                    : c.hiring_recommendation === 'Lean Hire'
                                    ? 'bg-sky-500/20 text-sky-400 border-sky-500/30'
                                    : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                                }`}
                              >
                                {c.hiring_recommendation || 'Pending'}
                              </span>
                            </td>
                            <td className="p-4">{c.modalities?.technical?.toFixed(1) ?? '—'}</td>
                            <td className="p-4">{c.modalities?.coding?.toFixed(1) ?? '—'}</td>
                            <td className="p-4">{c.modalities?.system_design?.toFixed(1) ?? '—'}</td>
                            <td className="p-4">{c.modalities?.behavioral?.toFixed(1) ?? '—'}</td>
                            <td className="p-4 text-xs">
                              <div>Conf: {(c.communication?.confidence * 100)?.toFixed(0)}%</div>
                              <div className="text-slate-500">{c.communication?.pace_wpm?.toFixed(0)} wpm</div>
                            </td>
                            <td className="p-4 font-bold text-blue-400">
                              +{c.growth_velocity.toFixed(2)}
                            </td>
                            <td className="p-4 text-right">
                              <button
                                onClick={() => handleOpenDebriefMemo(c.candidate_id)}
                                className="px-2.5 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 text-xs font-semibold rounded-lg border border-indigo-500/30 transition"
                              >
                                Memo
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center bg-slate-900 border border-slate-800 rounded-2xl text-slate-400">
                  Select a requisition with multiple candidates to inspect comparative decision matrices.
                </div>
              )}
            </div>
          )}

          {/* TAB 4: TALENT POOL */}
          {activeTab === 'talent' && (
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="text-lg font-bold text-white">Talent Pool Discovery</h3>
                  <p className="text-xs text-slate-400">
                    High-readiness candidates grounded across longitudinal sessions & learning velocity.
                  </p>
                </div>
                <button
                  onClick={handleSearchTalent}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition"
                >
                  Refresh Pool
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {talentPool.map((t) => (
                  <div key={t.candidate_id} className="p-5 bg-slate-900 border border-slate-800 rounded-2xl space-y-3">
                    <div className="flex justify-between items-start">
                      <div>
                        <div className="font-bold text-base text-slate-100">{t.full_name}</div>
                        <div className="text-xs text-slate-400">{t.email}</div>
                      </div>
                      <span className="px-2 py-0.5 text-xs font-bold rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {t.readiness_score?.toFixed(1)}% Ready
                      </span>
                    </div>

                    <div className="py-2 border-y border-slate-800 text-xs flex justify-between">
                      <span className="text-slate-400">Growth Velocity:</span>
                      <span className="font-bold text-blue-400">+{t.growth_velocity?.toFixed(2)} pts/mo</span>
                    </div>

                    <div className="text-xs text-slate-400">
                      <span className="font-semibold text-slate-300">Verified Skills:</span>{' '}
                      {t.verified_skills?.join(', ') || 'Distributed Systems, Python'}
                    </div>

                    {selectedReq && (
                      <button
                        onClick={async () => {
                          try {
                            await recruiterApi.inviteCandidate(selectedReq.id, t.candidate_id)
                            alert(`Invited ${t.full_name} to ${selectedReq.title}`)
                            await loadRequisitionData(selectedReq.id)
                          } catch {
                            alert('Failed to invite candidate')
                          }
                        }}
                        className="w-full mt-2 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5 text-indigo-400" />
                        Invite to {selectedReq.title}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 5: FUNNEL ANALYTICS */}
          {activeTab === 'analytics' && funnel && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Pipeline</div>
                  <div className="text-3xl font-extrabold text-indigo-400 mt-2">{funnel.total_pipeline}</div>
                </div>
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Time-to-Hire</div>
                  <div className="text-3xl font-extrabold text-emerald-400 mt-2">{funnel.avg_time_to_hire_days} days</div>
                </div>
                <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl text-center">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Offer Acceptance</div>
                  <div className="text-3xl font-extrabold text-blue-400 mt-2">{funnel.offer_acceptance_rate_pct}%</div>
                </div>
              </div>

              {/* Conversion Stages */}
              <div className="p-6 bg-slate-900 border border-slate-800 rounded-2xl space-y-4">
                <h3 className="text-sm font-bold uppercase text-slate-400 tracking-wider">Conversion Funnel Drop-off</h3>
                <div className="space-y-3">
                  {funnel.stages.map((st, idx) => (
                    <div key={idx} className="flex items-center gap-4">
                      <span className="w-36 text-xs font-semibold capitalize text-slate-300">
                        {st.stage.replace('_', ' ')}
                      </span>
                      <div className="flex-1 bg-slate-800 rounded-full h-3 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full rounded-full transition-all"
                          style={{ width: `${Math.min(st.conversion_rate_pct, 100)}%` }}
                        />
                      </div>
                      <span className="w-16 text-right text-xs font-bold text-slate-300">{st.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {/* MODAL 1: Create Requisition */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <form
            onSubmit={handleCreateRequisition}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl"
          >
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100">Create New Role Requisition</h3>
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Role Title</label>
              <input
                type="text"
                required
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Senior Distributed Systems Architect"
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Department</label>
              <input
                type="text"
                value={newDept}
                onChange={(e) => setNewDept(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Required Skills (comma separated)</label>
              <input
                type="text"
                value={newSkills}
                onChange={(e) => setNewSkills(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Hiring Score Cutoff (%)</label>
              <input
                type="number"
                min="50"
                max="95"
                value={newThreshold}
                onChange={(e) => setNewThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-600/20 transition"
              >
                Create Requisition
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 2: Edit Rubric Weights & Threshold */}
      {showEditWeightsModal && selectedReq && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <form
            onSubmit={handleSaveWeights}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-lg w-full space-y-4 shadow-2xl"
          >
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100">Calibrate Rubric & Cutoff</h3>
              <button
                type="button"
                onClick={() => setShowEditWeightsModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Technical Assessment Weight</span>
                  <span className="font-bold text-indigo-400">{weightsTech}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weightsTech}
                  onChange={(e) => setWeightsTech(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>System Design Weight</span>
                  <span className="font-bold text-indigo-400">{weightsSd}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weightsSd}
                  onChange={(e) => setWeightsSd(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Coding & Algorithms Weight</span>
                  <span className="font-bold text-indigo-400">{weightsCode}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weightsCode}
                  onChange={(e) => setWeightsCode(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div>
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Behavioral & Leadership Weight</span>
                  <span className="font-bold text-indigo-400">{weightsBehav}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={weightsBehav}
                  onChange={(e) => setWeightsBehav(Number(e.target.value))}
                  className="w-full accent-indigo-500"
                />
              </div>

              <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex justify-between items-center text-xs">
                <span className="text-slate-400">Total Rubric Weight:</span>
                <span
                  className={`font-bold ${
                    weightsTech + weightsSd + weightsCode + weightsBehav === 100
                      ? 'text-emerald-400'
                      : 'text-rose-400'
                  }`}
                >
                  {weightsTech + weightsSd + weightsCode + weightsBehav}% (Must equal 100%)
                </span>
              </div>

              <div className="pt-2 border-t border-slate-800">
                <div className="flex justify-between text-xs text-slate-300 mb-1">
                  <span>Hiring Qualification Threshold</span>
                  <span className="font-bold text-emerald-400">{editThreshold}%</span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="95"
                  value={editThreshold}
                  onChange={(e) => setEditThreshold(Number(e.target.value))}
                  className="w-full accent-emerald-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowEditWeightsModal(false)}
                className="px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={weightsTech + weightsSd + weightsCode + weightsBehav !== 100}
                className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium rounded-xl shadow-lg shadow-indigo-600/20 transition"
              >
                Save Calibration
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 3: Update Candidate Pipeline Stage */}
      {showStageUpdateModal && stageCandidate && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <form
            onSubmit={handleUpdateStageSubmit}
            className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-md w-full space-y-4 shadow-2xl"
          >
            <div className="flex justify-between items-center pb-2 border-b border-slate-800">
              <h3 className="text-lg font-bold text-slate-100">Update Pipeline Stage</h3>
              <button
                type="button"
                onClick={() => setShowStageUpdateModal(false)}
                className="text-slate-400 hover:text-slate-200"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">Target Stage</label>
              <select
                value={newStage}
                onChange={(e) => setNewStage(e.target.value as CandidateStage)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              >
                <option value="invited">Invited</option>
                <option value="in_progress">In Progress</option>
                <option value="interviewed">Interviewed</option>
                <option value="review_required">Review Required (Bar-Raiser)</option>
                <option value="offer">Offer Extended</option>
                <option value="rejected">Archived / Rejected</option>
              </select>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Recruiter Audit Notes (Optional)
              </label>
              <textarea
                rows={3}
                value={recruiterNote}
                onChange={(e) => setRecruiterNote(e.target.value)}
                placeholder="Document consensus from hiring committee, debrief findings, or next steps..."
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-sm text-slate-100 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-slate-800">
              <button
                type="button"
                onClick={() => setShowStageUpdateModal(false)}
                className="px-4 py-2 text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm bg-indigo-600 hover:bg-indigo-500 text-white font-medium rounded-xl shadow-lg shadow-indigo-600/20 transition"
              >
                Update Stage
              </button>
            </div>
          </form>
        </div>
      )}

      {/* MODAL 4: Executive Hiring Debrief Memo */}
      {showDebriefMemoModal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 max-w-3xl w-full max-h-[85vh] flex flex-col shadow-2xl space-y-4">
            <div className="flex justify-between items-center pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-indigo-400" />
                <h3 className="text-lg font-bold text-slate-100">Bar-Raiser Executive Hiring Debrief Memo</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => {
                    if (activeMemo?.memo_markdown) {
                      navigator.clipboard.writeText(activeMemo.memo_markdown)
                      setMemoCopied(true)
                      setTimeout(() => setMemoCopied(false), 2000)
                    }
                  }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl border border-slate-700 transition"
                >
                  {memoCopied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                  {memoCopied ? 'Copied' : 'Copy Markdown'}
                </button>
                <button
                  onClick={() => setShowDebriefMemoModal(false)}
                  className="text-slate-400 hover:text-slate-200"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {memoLoading ? (
              <div className="flex justify-center items-center py-20 text-slate-400 gap-3">
                <Clock className="w-5 h-5 animate-spin text-indigo-400" />
                <span>Synthesizing Bar-Raiser Debrief Memo with grounded telemetry...</span>
              </div>
            ) : activeMemo ? (
              <div className="overflow-y-auto space-y-4 pr-1 text-slate-200">
                {/* Meta Header */}
                <div className="p-4 bg-slate-950/70 border border-slate-800 rounded-2xl flex flex-wrap justify-between items-center gap-3">
                  <div>
                    <div className="font-bold text-base text-white">{activeMemo.candidate_name}</div>
                    <div className="text-xs text-slate-400">{activeMemo.role_title}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-[10px] text-slate-400 uppercase">Composite Score</div>
                      <div className="text-lg font-extrabold text-indigo-400">{activeMemo.composite_score.toFixed(1)}%</div>
                    </div>
                    <span
                      className={`px-3 py-1 text-xs font-bold rounded-xl border ${
                        activeMemo.hiring_recommendation === 'Hire' || activeMemo.hiring_recommendation === 'Strong Hire'
                          ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                          : activeMemo.hiring_recommendation === 'Lean Hire'
                          ? 'bg-sky-500/20 text-sky-400 border-sky-500/30'
                          : 'bg-rose-500/20 text-rose-400 border-rose-500/30'
                      }`}
                    >
                      {activeMemo.hiring_recommendation}
                    </span>
                  </div>
                </div>

                {/* Markdown Container */}
                <div className="p-5 bg-slate-950 border border-slate-800/80 rounded-2xl font-mono text-xs text-slate-300 leading-relaxed whitespace-pre-wrap select-text">
                  {activeMemo.memo_markdown}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  )
}
