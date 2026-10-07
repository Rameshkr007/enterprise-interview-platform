'use client'

import React, { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen,
  Calendar,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  RefreshCw,
  ExternalLink,
  Code,
  FileText,
  Video,
  FileCode,
  AlertCircle,
  Trophy,
  Brain,
  HelpCircle,
  Send,
  X,
  Plus,
  Flame,
  Zap,
  RotateCw,
  Layers,
  Award,
  ChevronRight,
  Eye,
  Check,
} from 'lucide-react'
import { learningApi, sm2LearningApi } from '@/lib/api'
import type {
  LearningPlan,
  LearningDaySchedule,
  ReassessmentQuizItem,
  SpacedRepetitionCard,
  SM2DeckStats,
  SM2ReviewResult,
} from '@/lib/types'

const QUALITY_BUTTONS = [
  { q: 0, label: '0: Blackout', sub: 'Complete failure', color: 'bg-rose-950/80 hover:bg-rose-900 border-rose-800 text-rose-300' },
  { q: 1, label: '1: Incorrect', sub: 'Remembered upon reveal', color: 'bg-rose-900/40 hover:bg-rose-800/60 border-rose-700/60 text-rose-200' },
  { q: 2, label: '2: Hard Miss', sub: 'Almost remembered', color: 'bg-amber-950/60 hover:bg-amber-900/80 border-amber-800 text-amber-300' },
  { q: 3, label: '3: Difficult', sub: 'Correct with difficulty', color: 'bg-blue-950/60 hover:bg-blue-900/80 border-blue-800 text-blue-300' },
  { q: 4, label: '4: Good Recall', sub: 'Hesitated briefly', color: 'bg-emerald-950/60 hover:bg-emerald-900/80 border-emerald-800 text-emerald-300' },
  { q: 5, label: '5: Perfect', sub: 'Instant recall', color: 'bg-emerald-900/80 hover:bg-emerald-800 border-emerald-600 text-emerald-100 font-bold' },
]

function LearningEngineContent() {
  const searchParams = useSearchParams()
  const initialFocus = searchParams.get('focus') || ''

  // Navigation mode
  const [activeTab, setActiveTab] = useState<'plans' | 'sm2' | 'deck'>('plans')

  // Plans state
  const [plans, setPlans] = useState<LearningPlan[]>([])
  const [selectedPlan, setSelectedPlan] = useState<LearningPlan | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Plan generation modal state
  const [isGenerating, setIsGenerating] = useState(false)
  const [skillInput, setSkillInput] = useState(initialFocus)
  const [roleInput, setRoleInput] = useState('')
  const [generateLoading, setGenerateLoading] = useState(false)

  // Reassessment modal state
  const [reassessOpen, setReassessOpen] = useState(false)
  const [reassessAnswers, setReassessAnswers] = useState<Record<string, string>>({})
  const [reassessSubmitting, setReassessSubmitting] = useState(false)
  const [reassessResult, setReassessResult] = useState<{
    reassessment_score: number
    status: string
    gap_resolved: boolean
  } | null>(null)

  // ── SM-2 Spaced Repetition State ──────────────────────────────────────────
  const [dueCards, setDueCards] = useState<SpacedRepetitionCard[]>([])
  const [activeCardIndex, setActiveCardIndex] = useState<number>(0)
  const [isFlipped, setIsFlipped] = useState<boolean>(false)
  const [deckStats, setDeckStats] = useState<SM2DeckStats | null>(null)
  const [allDeckCards, setAllDeckCards] = useState<SpacedRepetitionCard[]>([])
  const [selectedTierFilter, setSelectedTierFilter] = useState<number | 'all'>('all')
  const [sm2Loading, setSm2Loading] = useState<boolean>(false)
  const [reviewSubmitting, setReviewSubmitting] = useState<boolean>(false)
  const [lastReviewResult, setLastReviewResult] = useState<SM2ReviewResult | null>(null)

  const loadPlans = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await learningApi.getMyPlans()
      setPlans(data)
      if (data.length > 0) {
        setSelectedPlan(data[0])
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load learning plans'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }

  const loadSM2Data = async () => {
    try {
      setSm2Loading(true)
      const [due, stats, deck] = await Promise.all([
        sm2LearningApi.getDueCards(25),
        sm2LearningApi.getStats(),
        sm2LearningApi.getDeck(),
      ])
      setDueCards(due)
      setDeckStats(stats)
      setAllDeckCards(deck)
      setActiveCardIndex(0)
      setIsFlipped(false)
      setLastReviewResult(null)
    } catch (err) {
      console.error('Failed to load SM-2 flashcard data', err)
    } finally {
      setSm2Loading(false)
    }
  }

  useEffect(() => {
    loadPlans()
    loadSM2Data()
  }, [])

  useEffect(() => {
    if (initialFocus) {
      setSkillInput(initialFocus)
      setIsGenerating(true)
    }
  }, [initialFocus])

  const handleGeneratePlan = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!skillInput.trim()) return

    try {
      setGenerateLoading(true)
      const newPlan = await learningApi.generatePlan({
        skill_name: skillInput.trim(),
        target_role: roleInput.trim() || undefined,
      })
      setPlans((prev) => [newPlan, ...prev])
      setSelectedPlan(newPlan)
      setIsGenerating(false)
      setSkillInput('')
      setRoleInput('')
    } catch (err: unknown) {
      console.error('Plan generation failed:', err)
      alert(err instanceof Error ? err.message : 'Plan generation failed')
    } finally {
      setGenerateLoading(false)
    }
  }

  const handleCompleteMilestone = async (planId: string, day: number) => {
    try {
      const updated = await learningApi.completeMilestone(planId, day)
      setSelectedPlan(updated)
      setPlans((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
    } catch (err: unknown) {
      console.error('Failed to complete milestone:', err)
    }
  }

  const handleReassessSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedPlan) return

    try {
      setReassessSubmitting(true)
      const res = await learningApi.submitReassessment(selectedPlan.id, reassessAnswers)
      setReassessResult(res)
      const refreshed = await learningApi.getPlan(selectedPlan.id)
      setSelectedPlan(refreshed)
      setPlans((prev) => prev.map((p) => (p.id === refreshed.id ? refreshed : p)))
    } catch (err: unknown) {
      console.error('Reassessment failed:', err)
      alert(err instanceof Error ? err.message : 'Reassessment failed')
    } finally {
      setReassessSubmitting(false)
    }
  }

  // ── SM-2 Review Action ────────────────────────────────────────────────────
  const handleQualityReview = async (quality: number) => {
    if (!dueCards[activeCardIndex] || reviewSubmitting) return

    try {
      setReviewSubmitting(true)
      const currentCard = dueCards[activeCardIndex]
      const result = await sm2LearningApi.submitReview({
        card_id: currentCard.id,
        quality,
      })
      setLastReviewResult(result)

      // Refresh deck stats in background
      sm2LearningApi.getStats().then((s) => setDeckStats(s))

      // Advance to next card or complete
      setTimeout(() => {
        setIsFlipped(false)
        setActiveCardIndex((prev) => prev + 1)
        setReviewSubmitting(false)
      }, 700)
    } catch (err) {
      console.error('Failed to submit SM-2 review', err)
      setReviewSubmitting(false)
    }
  }

  const handleSeedCanonical = async () => {
    try {
      setSm2Loading(true)
      await sm2LearningApi.seedDeck()
      await loadSM2Data()
    } catch (err) {
      console.error('Failed to seed deck', err)
    } finally {
      setSm2Loading(false)
    }
  }

  const currentDueCard = dueCards[activeCardIndex]
  const isDeckCompleted = dueCards.length > 0 && activeCardIndex >= dueCards.length

  const filteredDeckCards = allDeckCards.filter((c) => {
    if (selectedTierFilter === 'all') return true
    return c.tier === selectedTierFilter
  })

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'video':
        return <Video className="w-4 h-4 text-rose-400" />
      case 'paper':
        return <FileCode className="w-4 h-4 text-purple-400" />
      case 'documentation':
        return <Code className="w-4 h-4 text-cyan-400" />
      default:
        return <FileText className="w-4 h-4 text-blue-400" />
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium mb-1">
              <BookOpen className="w-4 h-4" />
              <span>Personalized Learning & Spaced Repetition Engine</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Adaptive Mastery & SM-2 Retrieval
              <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-normal">
                Ebbinghaus Decay Protection
              </span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Synthesize 7-day milestone curricula and reinforce critical system design, concurrency, and architecture knowledge with SuperMemo-2 spaced intervals.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsGenerating(true)}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white shadow-lg shadow-cyan-950 transition flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              Generate 7-Day Plan
            </button>
            <Link
              href="/skills"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-2"
            >
              <Layers className="w-4 h-4 text-cyan-400" />
              Skill DAG Explorer
            </Link>
          </div>
        </div>

        {/* Global SM-2 Metrics HUD */}
        {deckStats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 rounded-xl bg-slate-900 border border-slate-800 text-xs">
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1">
                <Flame className="w-3.5 h-3.5 text-amber-500" /> Review Streak
              </span>
              <p className="text-lg font-bold text-amber-400 mt-1">{deckStats.current_streak_days} Days</p>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5 text-rose-400" /> Due Today
              </span>
              <p className="text-lg font-bold text-rose-400 mt-1">{deckStats.due_today_count} Cards</p>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Mature Cards
              </span>
              <p className="text-lg font-bold text-emerald-400 mt-1">{deckStats.mature_cards_count} (≥21d)</p>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1">
                <Zap className="w-3.5 h-3.5 text-cyan-400" /> Retention Rate
              </span>
              <p className="text-lg font-bold text-cyan-400 mt-1">{deckStats.average_retention_pct}%</p>
            </div>
            <div className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/60">
              <span className="text-slate-400 flex items-center gap-1">
                <Trophy className="w-3.5 h-3.5 text-purple-400" /> Total Reviews
              </span>
              <p className="text-lg font-bold text-purple-300 mt-1">{deckStats.total_reviews_completed}</p>
            </div>
          </div>
        )}

        {/* Tab Switcher */}
        <div className="flex items-center space-x-3 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveTab('plans')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'plans'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Calendar className="w-4 h-4" />
            <span>7-Day Mastery Curricula</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('sm2')
              if (dueCards.length === 0) loadSM2Data()
            }}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'sm2'
                ? 'bg-purple-500/20 text-purple-300 border border-purple-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span>SM-2 Spaced Flashcards ({dueCards.length} Due)</span>
          </button>

          <button
            onClick={() => {
              setActiveTab('deck')
              if (allDeckCards.length === 0) loadSM2Data()
            }}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-semibold transition ${
              activeTab === 'deck'
                ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
            }`}
          >
            <Layers className="w-4 h-4" />
            <span>Flashcard Library ({allDeckCards.length})</span>
          </button>
        </div>

        {/* ── TAB 1: 7-DAY MASTERY CURRICULA ──────────────────────────────────── */}
        {activeTab === 'plans' && (
          <>
            {loading ? (
              <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
                <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
                <p className="text-sm">Loading personalized curricula...</p>
              </div>
            ) : error ? (
              <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-300 space-y-3">
                <div className="flex items-center gap-2 font-semibold">
                  <AlertCircle className="w-5 h-5 text-rose-400" />
                  <span>Failed to Load Learning Engine</span>
                </div>
                <p className="text-sm text-rose-300/80">{error}</p>
                <button
                  onClick={loadPlans}
                  className="text-xs px-3 py-1.5 rounded-md bg-rose-900/60 hover:bg-rose-900 border border-rose-700 text-rose-200"
                >
                  Retry
                </button>
              </div>
            ) : plans.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-slate-900/50 border border-slate-800 space-y-4">
                <Sparkles className="w-12 h-12 text-cyan-500 mx-auto" />
                <h3 className="text-lg font-medium text-slate-300">No Learning Plans Generated Yet</h3>
                <p className="text-sm text-slate-500 max-w-md mx-auto">
                  Generate your first 7-day personalized mastery plan targeted at an interview skill gap or domain.
                </p>
                <button
                  onClick={() => setIsGenerating(true)}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-sm font-medium transition"
                >
                  <Plus className="w-4 h-4" />
                  Generate 7-Day Plan
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
                {/* Sidebar Plans List */}
                <div className="space-y-4 lg:col-span-1">
                  <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    <span>Active Plans ({plans.length})</span>
                    <button
                      onClick={() => setIsGenerating(true)}
                      className="text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>New</span>
                    </button>
                  </div>

                  <div className="space-y-2">
                    {plans.map((p) => {
                      const completedDays = p.daily_schedule.filter((d) => d.is_completed).length
                      const pct = Math.round((completedDays / p.target_completion_days) * 100)
                      const isSelected = selectedPlan?.id === p.id

                      return (
                        <div
                          key={p.id}
                          onClick={() => setSelectedPlan(p)}
                          className={`p-4 rounded-xl cursor-pointer border transition ${
                            isSelected
                              ? 'bg-slate-900 border-cyan-500 shadow-md shadow-cyan-950/40'
                              : 'bg-slate-900/50 hover:bg-slate-900/80 border-slate-800 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-cyan-400">{p.category}</span>
                            <span
                              className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-semibold ${
                                p.status === 'completed'
                                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                  : 'bg-slate-800 text-slate-300'
                              }`}
                            >
                              {p.status}
                            </span>
                          </div>
                          <h4 className="text-sm font-medium text-white mt-1.5 line-clamp-1">{p.title}</h4>
                          <div className="mt-3">
                            <div className="flex justify-between text-[11px] text-slate-500 mb-1">
                              <span>Progress</span>
                              <span>
                                {completedDays}/{p.target_completion_days} Days ({pct}%)
                              </span>
                            </div>
                            <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                              <div
                                className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                                style={{ width: `${pct}%` }}
                              />
                            </div>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Main Plan View & 7-Day Roadmap */}
                {selectedPlan && (
                  <div className="space-y-6 lg:col-span-3">
                    {/* Plan Hero Card */}
                    <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 space-y-4">
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800 font-semibold">
                              {selectedPlan.category}
                            </span>
                            <span className="text-xs text-slate-500">
                              Target Gap: <strong className="text-slate-300">{selectedPlan.detected_gap}</strong>
                            </span>
                          </div>
                          <h2 className="text-2xl font-bold text-white mt-2">{selectedPlan.title}</h2>
                        </div>

                        {selectedPlan.reassessment_quiz && selectedPlan.reassessment_quiz.length > 0 && (
                          <button
                            onClick={() => {
                              setReassessResult(null)
                              setReassessAnswers({})
                              setReassessOpen(true)
                            }}
                            className="px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow-lg shadow-emerald-950 flex items-center gap-2 transition whitespace-nowrap"
                          >
                            <Trophy className="w-4 h-4" />
                            Take 5-Point Reassessment
                          </button>
                        )}
                      </div>

                      {/* Daily Schedule Cards */}
                      <div className="space-y-4 pt-4 border-t border-slate-800/80">
                        {selectedPlan.daily_schedule.map((day) => {
                          return (
                            <div
                              key={day.day}
                              className={`p-5 rounded-xl border transition ${
                                day.is_completed
                                  ? 'bg-slate-900/40 border-slate-800 opacity-90'
                                  : 'bg-slate-900/90 border-slate-700/80'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-3">
                                <div className="flex items-center gap-3">
                                  <span
                                    className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                                      day.is_completed
                                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                                        : 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/40'
                                    }`}
                                  >
                                    D{day.day}
                                  </span>
                                  <h3 className="text-base font-semibold text-white">{day.theme}</h3>
                                </div>
                                <button
                                  onClick={() => handleCompleteMilestone(selectedPlan.id, day.day)}
                                  className={`px-3 py-1 rounded-lg text-xs font-medium flex items-center gap-1.5 transition ${
                                    day.is_completed
                                      ? 'bg-emerald-950 border border-emerald-800 text-emerald-300'
                                      : 'bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700'
                                  }`}
                                >
                                  <CheckCircle2 className="w-3.5 h-3.5" />
                                  {day.is_completed ? 'Completed' : 'Mark Completed'}
                                </button>
                              </div>

                              {/* Objectives */}
                              <div className="space-y-1.5 mb-3">
                                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                                  Learning Objectives:
                                </span>
                                <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                                  {day.objectives.map((obj, oIdx) => (
                                    <li key={oIdx}>{obj}</li>
                                  ))}
                                </ul>
                              </div>

                              {/* Reading Resources */}
                              {day.reading_resources && day.reading_resources.length > 0 && (
                                <div className="space-y-1.5 pt-3 border-t border-slate-800/60">
                                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                                    Curated Reading:
                                  </span>
                                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {day.reading_resources.map((res, rIdx) => (
                                      <a
                                        key={rIdx}
                                        href={res.ref}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 hover:border-cyan-500/40 flex items-center justify-between text-xs text-slate-300 transition group"
                                      >
                                        <div className="flex items-center gap-2">
                                          {getResourceIcon(res.type)}
                                          <span className="font-medium group-hover:text-cyan-300 transition line-clamp-1">
                                            {res.title}
                                          </span>
                                        </div>
                                        <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-cyan-400" />
                                      </a>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {/* ── TAB 2: SM-2 SPACED REPETITION STUDIO ───────────────────────────── */}
        {activeTab === 'sm2' && (
          <div className="max-w-3xl mx-auto space-y-6">
            {sm2Loading ? (
              <div className="h-80 flex flex-col items-center justify-center gap-3 text-slate-400">
                <RefreshCw className="w-8 h-8 animate-spin text-purple-500" />
                <p className="text-sm">Loading active SM-2 review queue...</p>
              </div>
            ) : isDeckCompleted || dueCards.length === 0 ? (
              <div className="p-12 text-center rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
                <CheckCircle2 className="w-14 h-14 text-emerald-400 mx-auto" />
                <h3 className="text-xl font-bold text-white">Daily Review Queue Clear!</h3>
                <p className="text-sm text-slate-400 max-w-md mx-auto">
                  You have reviewed all due flashcards for today. The SuperMemo-2 algorithm will schedule your next retrieval session when memory stability decays.
                </p>
                <div className="pt-2 flex justify-center gap-3">
                  <button
                    onClick={loadSM2Data}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-2"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    Check for Due Cards
                  </button>
                  <button
                    onClick={handleSeedCanonical}
                    className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-2"
                  >
                    <Sparkles className="w-3.5 h-3.5" />
                    Add More Skill Cards
                  </button>
                </div>
              </div>
            ) : currentDueCard ? (
              <div className="space-y-6">
                {/* Progress bar */}
                <div className="flex items-center justify-between text-xs text-slate-400">
                  <span>
                    Card {activeCardIndex + 1} of {dueCards.length}
                  </span>
                  <span>
                    Tier {currentDueCard.tier} • {currentDueCard.category}
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                    style={{ width: `${Math.round(((activeCardIndex + 1) / dueCards.length) * 100)}%` }}
                  />
                </div>

                {/* Interactive Flip Card */}
                <div
                  onClick={() => setIsFlipped(!isFlipped)}
                  className="min-h-[300px] p-8 rounded-2xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-950 border border-slate-800 hover:border-purple-500/50 transition cursor-pointer shadow-xl relative flex flex-col justify-between select-none"
                >
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                        Tier {currentDueCard.tier} Flashcard
                      </span>
                      <span className="text-xs text-slate-500 flex items-center gap-1">
                        <RotateCw className="w-3 h-3 text-purple-400" />
                        Click anywhere to flip
                      </span>
                    </div>

                    <h3 className="text-xl font-bold text-white pt-2">{currentDueCard.title}</h3>

                    {!isFlipped ? (
                      <div className="pt-4">
                        <span className="text-xs text-purple-400 font-semibold uppercase tracking-wider block mb-1">
                          Retrieval Prompt:
                        </span>
                        <p className="text-base text-slate-200 leading-relaxed font-medium">
                          {currentDueCard.question_prompt}
                        </p>
                      </div>
                    ) : (
                      <div className="pt-4 space-y-4 animate-fadeIn">
                        <div>
                          <span className="text-xs text-emerald-400 font-semibold uppercase tracking-wider block mb-1">
                            Technical Explanation:
                          </span>
                          <p className="text-sm text-slate-200 leading-relaxed">
                            {currentDueCard.answer_explanation}
                          </p>
                        </div>
                        {currentDueCard.key_takeaway && (
                          <div className="p-3.5 rounded-lg bg-purple-950/30 border border-purple-800/40 text-xs text-purple-200">
                            <strong>Key Takeaway:</strong> {currentDueCard.key_takeaway}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="pt-6 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-500">
                    <span>
                      Current Interval: <strong className="text-slate-300">{currentDueCard.interval_days}d</strong>
                    </span>
                    <span>
                      Easiness Factor: <strong className="text-slate-300">{currentDueCard.easiness_factor.toFixed(2)}</strong>
                    </span>
                    <span>
                      Repetitions: <strong className="text-slate-300">{currentDueCard.repetition_count}</strong>
                    </span>
                  </div>
                </div>

                {/* Rating Buttons (Shown when flipped) */}
                {isFlipped ? (
                  <div className="space-y-3">
                    <span className="text-xs font-semibold text-slate-400 block text-center uppercase tracking-wider">
                      Rate Your Recall Quality (SuperMemo-2):
                    </span>
                    <div className="grid grid-cols-2 md:grid-cols-6 gap-2">
                      {QUALITY_BUTTONS.map((btn) => (
                        <button
                          key={btn.q}
                          disabled={reviewSubmitting}
                          onClick={() => handleQualityReview(btn.q)}
                          className={`p-3 rounded-xl border text-center transition flex flex-col items-center justify-center gap-1 ${btn.color} disabled:opacity-50`}
                        >
                          <span className="text-xs font-bold">{btn.label}</span>
                          <span className="text-[10px] opacity-75">{btn.sub}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center">
                    <button
                      onClick={() => setIsFlipped(true)}
                      className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold transition flex items-center gap-2 mx-auto"
                    >
                      <Eye className="w-4 h-4" />
                      Reveal Technical Answer
                    </button>
                  </div>
                )}

                {/* Immediate Review Feedback Toast */}
                {lastReviewResult && (
                  <div className="p-3.5 rounded-xl bg-slate-900 border border-purple-500/40 text-xs flex items-center justify-between text-slate-200">
                    <span>
                      Recorded Quality <strong>{lastReviewResult.quality}/5</strong> • Next Review in{' '}
                      <strong className="text-purple-300">+{lastReviewResult.interval_days} days</strong>
                    </span>
                    {lastReviewResult.mastery_boost_applied > 0 && (
                      <span className="text-emerald-400 font-bold">
                        +{lastReviewResult.mastery_boost_applied} Skill Mastery Boost
                      </span>
                    )}
                  </div>
                )}
              </div>
            ) : null}
          </div>
        )}

        {/* ── TAB 3: FLASHCARD DECK LIBRARY ──────────────────────────────────── */}
        {activeTab === 'deck' && (
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Tier:</span>
                {(['all', 1, 2, 3, 4, 5] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setSelectedTierFilter(t)}
                    className={`px-2.5 py-1 rounded text-xs font-medium transition ${
                      selectedTierFilter === t
                        ? 'bg-purple-600 text-white font-bold'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                    }`}
                  >
                    {t === 'all' ? 'All Tiers' : `T${t}`}
                  </button>
                ))}
              </div>

              <button
                onClick={handleSeedCanonical}
                className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 text-xs font-semibold flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" />
                Seed Canonical Cards
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredDeckCards.map((c) => (
                <div
                  key={c.id}
                  className="p-5 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 flex flex-col justify-between space-y-3"
                >
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                        Tier {c.tier}
                      </span>
                      <span className="text-[11px] text-slate-400">{c.category}</span>
                    </div>
                    <h4 className="text-sm font-bold text-white line-clamp-1">{c.title}</h4>
                    <p className="text-xs text-slate-400 mt-2 line-clamp-3">{c.question_prompt}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                    <span>Interval: {c.interval_days}d</span>
                    <span>EF: {c.easiness_factor.toFixed(2)}</span>
                    <span className="text-purple-400">{c.repetition_count} reps</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── MODALS: REASSESSMENT & GENERATION ──────────────────────────────── */}
        <AnimatePresence>
          {reassessOpen && selectedPlan && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-2xl max-h-[90vh] overflow-y-auto rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-6 shadow-2xl"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider">
                      Mastery Validation
                    </span>
                    <h3 className="text-xl font-bold text-white mt-1">5-Point Reassessment Quiz</h3>
                  </div>
                  <button
                    onClick={() => setReassessOpen(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                {reassessResult ? (
                  <div className="space-y-4 text-center py-6">
                    <Trophy className="w-16 h-16 text-emerald-400 mx-auto" />
                    <h4 className="text-2xl font-bold text-white">
                      Score: {reassessResult.reassessment_score}%
                    </h4>
                    <p className="text-sm text-slate-300">
                      {reassessResult.gap_resolved
                        ? 'Congratulations! You have resolved this skill deficiency and updated your AI Twin.'
                        : 'Review the objectives and retry to achieve passing threshold (70%).'}
                    </p>
                    <button
                      onClick={() => setReassessOpen(false)}
                      className="px-6 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold"
                    >
                      Close Reassessment
                    </button>
                  </div>
                ) : (
                  <form onSubmit={handleReassessSubmit} className="space-y-6">
                    <div className="space-y-4">
                      {selectedPlan.reassessment_quiz?.map((q, idx) => (
                        <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <span className="text-xs font-bold text-cyan-400">Question {idx + 1}</span>
                            <span className="text-[10px] text-slate-500">Max: {q.max_points} pts</span>
                          </div>
                          <p className="text-sm font-medium text-slate-200">{q.question}</p>
                          <textarea
                            rows={3}
                            required
                            placeholder="Type your technical response here..."
                            value={reassessAnswers[String(q.id || idx)] || ''}
                            onChange={(e) =>
                              setReassessAnswers({
                                ...reassessAnswers,
                                [String(q.id || idx)]: e.target.value,
                              })
                            }
                            className="w-full px-3 py-2 rounded-lg bg-slate-900 border border-slate-800 text-white text-xs placeholder-slate-600 focus:outline-none focus:border-cyan-500"
                          />
                        </div>
                      ))}
                    </div>

                    <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                      <button
                        type="button"
                        onClick={() => setReassessOpen(false)}
                        className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        disabled={reassessSubmitting}
                        className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-lg shadow-emerald-950 transition flex items-center gap-2 disabled:opacity-50"
                      >
                        {reassessSubmitting ? 'Evaluating...' : 'Submit Reassessment'}
                      </button>
                    </div>
                  </form>
                )}
              </motion.div>
            </div>
          )}

          {isGenerating && (
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 space-y-6 shadow-2xl"
              >
                <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                  <h3 className="text-lg font-bold text-white">Generate 7-Day Curriculum</h3>
                  <button
                    onClick={() => setIsGenerating(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleGeneratePlan} className="space-y-4">
                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Skill Gap / Topic:</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Distributed Consensus (Raft/Paxos)"
                      value={skillInput}
                      onChange={(e) => setSkillInput(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div>
                    <label className="text-xs text-slate-400 block mb-1">Target Role (Optional):</label>
                    <input
                      type="text"
                      placeholder="e.g. Senior Backend Engineer (L5)"
                      value={roleInput}
                      onChange={(e) => setRoleInput(e.target.value)}
                      className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-800 text-white text-xs outline-none focus:border-cyan-500"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => setIsGenerating(false)}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={generateLoading}
                      className="px-5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-2 disabled:opacity-50"
                    >
                      {generateLoading ? 'Synthesizing...' : 'Generate Plan'}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default function LearningEnginePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400">
          <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
        </div>
      }
    >
      <LearningEngineContent />
    </Suspense>
  )
}
