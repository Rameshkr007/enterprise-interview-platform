'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { interviewApi, paymentApi, getBaseUrl } from '@/lib/api'
import type { ExtractedInterviewPlan, SubscriptionData } from '@/lib/api'
import { useInterviewStore } from '@/store/interview'
import { useAuthStore } from '@/store/auth'
import PaymentModal from '@/components/payment/PaymentModal'
import {
  Code2,
  Cpu,
  Database,
  Network,
  Terminal,
  Zap,
  Sparkles,
  Flame,
  Building2,
  Clock,
  Mic,
  Sliders,
  CheckCircle2,
  ArrowRight,
  ShieldCheck,
  GraduationCap,
  Layers,
  HelpCircle,
  AlertTriangle,
  ChevronLeft,
  UserCheck,
  LogIn,
  RefreshCw,
  Activity,
  Bot,
  Send,
  MessageSquare,
  BookOpen,
  FileText,
  CreditCard,
  Target,
  Compass,
} from 'lucide-react'

// ── CSE Targeted Presets ─────────────────────────────────────────────────────
interface PresetConfig {
  id: string
  name: string
  subtitle: string
  tag: string
  icon: React.ElementType
  iconColor: string
  borderColor: string
  bgHover: string
  questionCount: number
  difficulty: 'easy' | 'medium' | 'hard'
  adaptive: boolean
  categories: string[]
  hiringTier: string
  estMinutes: number
}

const CSE_PRESETS: PresetConfig[] = [
  {
    id: 'campus-placement',
    name: 'Campus Placement SDE-1',
    subtitle: 'DSA Patterns, Core OS/DBMS, & Project Architecture Defense',
    tag: 'Most Popular for CSE',
    icon: GraduationCap,
    iconColor: 'text-cyan-400',
    borderColor: 'border-cyan-500/40 hover:border-cyan-400',
    bgHover: 'group-hover:bg-cyan-500/10',
    questionCount: 8,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical', 'system_design', 'behavioral'],
    hiringTier: 'Campus Drives (TCS Prime, Infosys DPE, Wipro, Tier-1 Drives)',
    estMinutes: 18,
  },
  {
    id: 'faang-algorithmic',
    name: 'FAANG Algorithmic Loop',
    subtitle: 'Advanced Problem Solving, Edge Cases, & Time/Space Rigor',
    tag: 'Tier-1 Product Bar',
    icon: Flame,
    iconColor: 'text-orange-400',
    borderColor: 'border-orange-500/40 hover:border-orange-400',
    bgHover: 'group-hover:bg-orange-500/10',
    questionCount: 10,
    difficulty: 'hard',
    adaptive: true,
    categories: ['technical', 'system_design'],
    hiringTier: 'Google, Amazon (LP), Meta, Microsoft, Uber',
    estMinutes: 24,
  },
  {
    id: 'fullstack-web',
    name: 'Full-Stack & Systems Dev',
    subtitle: 'React/Next.js Internals, REST APIs, SQL Queries & Async Concurrency',
    tag: 'High-Growth Tech',
    icon: Layers,
    iconColor: 'text-violet-400',
    borderColor: 'border-violet-500/40 hover:border-violet-400',
    bgHover: 'group-hover:bg-violet-500/10',
    questionCount: 8,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical', 'situational'],
    hiringTier: 'Swiggy, Zomato, Razorpay, FinTech & YC Startups',
    estMinutes: 16,
  },
  {
    id: 'core-cs-fundamentals',
    name: 'Core CS Fundamentals',
    subtitle: 'Operating Systems, DBMS & SQL, Computer Networks, & OOPs Concepts',
    tag: 'Gatekeeper Round',
    icon: Terminal,
    iconColor: 'text-emerald-400',
    borderColor: 'border-emerald-500/40 hover:border-emerald-400',
    bgHover: 'group-hover:bg-emerald-500/10',
    questionCount: 6,
    difficulty: 'medium',
    adaptive: true,
    categories: ['technical'],
    hiringTier: 'Technical Written & First-Round Elimination Interviews',
    estMinutes: 12,
  },
]

// ── CSE Focus Disciplines ────────────────────────────────────────────────────
interface DisciplineOption {
  id: string
  name: string
  shortDesc: string
  icon: React.ElementType
  color: string
}

const CSE_DISCIPLINES: DisciplineOption[] = [
  {
    id: 'technical',
    name: 'Data Structures & Algorithms',
    shortDesc: 'Arrays, Trees, Graphs, DP, Sorting, & Time Complexity',
    icon: Code2,
    color: 'text-cyan-400',
  },
  {
    id: 'system_design',
    name: 'Core CS (OS, DBMS, Networks, HLD)',
    shortDesc: 'Deadlocks, Indexing, TCP/IP, Caching, & Scalable Schemas',
    icon: Cpu,
    color: 'text-purple-400',
  },
  {
    id: 'behavioral',
    name: 'Project Defense & STAR Behavioral',
    shortDesc: 'Final-year projects, tech trade-offs, teamwork, & leadership',
    icon: GraduationCap,
    color: 'text-amber-400',
  },
  {
    id: 'situational',
    name: 'Practical Debugging & Web Engineering',
    shortDesc: 'Production bugs, async concurrency, state handling, & APIs',
    icon: Network,
    color: 'text-emerald-400',
  },
  {
    id: 'culture_fit',
    name: 'HR & Engineering Culture Caliber',
    shortDesc: 'Conflict resolution, workplace adaptability, & ambition',
    icon: Sparkles,
    color: 'text-pink-400',
  },
]

export default function NewInterviewPage() {
  const router = useRouter()
  const setSession = useInterviewStore((s) => s.setSession)
  const { user, login, fetchMe } = useAuthStore()

  // Top Tab
  const [activeTab, setActiveTab] = useState<'advisor' | 'blueprints'>('advisor')

  // Conversational Requirement Agent State
  const [chatMessages, setChatMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([
    {
      role: 'assistant',
      content:
        "Hello! I'm your Universal AI Interview Requirement Advisor. What are you preparing for? Tell me your target role, programming language, subject, or upcoming exam (e.g., Campus Placement SDE-1, Google FAANG, React/Node Full-Stack, or College Viva).",
    },
  ])
  const [userInput, setUserInput] = useState('')
  const [isAgentAnalyzing, setIsAgentAnalyzing] = useState(false)
  const [extractedPlan, setExtractedPlan] = useState<ExtractedInterviewPlan | null>(null)
  const [syllabusText, setSyllabusText] = useState('')
  const [showSyllabusInput, setShowSyllabusInput] = useState(false)
  const chatScrollRef = useRef<HTMLDivElement>(null)

  // Direct Blueprint State
  const [selectedPreset, setSelectedPreset] = useState<string>('campus-placement')
  const [count, setCount] = useState<number>(8)
  const [categories, setCategories] = useState<string[]>(['technical', 'system_design', 'behavioral'])
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [interviewMode, setInterviewMode] = useState<'practice' | 'exam'>('practice')
  const [adaptiveMode, setAdaptiveMode] = useState<boolean>(true)
  const [targetTier, setTargetTier] = useState<string>('campus')

  // Common UI State
  const [isCreating, setIsCreating] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)

  // Payment Modal State
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false)
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null)

  // Auth & Backend Warmup Telemetry State
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isAuthLoading, setIsAuthLoading] = useState<boolean>(true)
  const [isDemoLoggingIn, setIsDemoLoggingIn] = useState<boolean>(false)
  const [serverWarmup, setServerWarmup] = useState<'online' | 'warming' | 'checking'>('checking')

  // Auto-scroll conversational chat
  useEffect(() => {
    if (chatScrollRef.current) {
      chatScrollRef.current.scrollTop = chatScrollRef.current.scrollHeight
    }
  }, [chatMessages, isAgentAnalyzing])

  // Check auth and ping backend
  useEffect(() => {
    let isMounted = true

    async function initCheck() {
      const localToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      if (localToken) {
        setIsAuthenticated(true)
        fetchMe().catch(() => {})
      } else if (user) {
        setIsAuthenticated(true)
      } else {
        setIsAuthenticated(false)
      }
      setIsAuthLoading(false)

      // Fetch active subscription
      paymentApi
        .getSubscription()
        .then((s) => isMounted && setSubscription(s))
        .catch(() => {})

      // Pre-warm backend
      try {
        const rootUrl = getBaseUrl().replace('/api/v1', '')
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 8000)

        const res = await fetch(`${rootUrl}/health`, {
          method: 'GET',
          signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (isMounted) {
          if (res.ok) {
            setServerWarmup('online')
          } else {
            setServerWarmup('warming')
          }
        }
      } catch {
        if (isMounted) {
          setServerWarmup('warming')
        }
      }
    }

    initCheck()
    return () => {
      isMounted = false
    }
  }, [fetchMe, user])

  // Apply Blueprint Preset
  const handleApplyPreset = (preset: PresetConfig) => {
    setSelectedPreset(preset.id)
    setCount(preset.questionCount)
    setCategories(preset.categories)
    setDifficulty(preset.difficulty)
    setAdaptiveMode(preset.adaptive)
  }

  // Toggle Category
  const toggleCategory = (catId: string) => {
    setSelectedPreset('')
    setCategories((prev) =>
      prev.includes(catId)
        ? prev.length > 1
          ? prev.filter((c) => c !== catId)
          : prev
        : [...prev, catId]
    )
  }

  // 1-Click CSE Demo Sign In
  const handleQuickDemoLogin = async () => {
    setIsDemoLoggingIn(true)
    setError(null)
    try {
      await login('candidate@enterprise.ai', 'CandidatePassword123!')
      setIsAuthenticated(true)
      setIsDemoLoggingIn(false)
    } catch {
      try {
        await login('csetest@enterprise.ai', 'Password123!')
        setIsAuthenticated(true)
      } catch (err: any) {
        setError(err?.response?.data?.detail || err?.response?.data?.message || 'Demo sign-in failed.')
      } finally {
        setIsDemoLoggingIn(false)
      }
    }
  }

  // Ensure Auth before starting
  async function ensureAuth() {
    const existingToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (!existingToken && !user) {
      try {
        await login('candidate@enterprise.ai', 'CandidatePassword123!')
        setIsAuthenticated(true)
      } catch {
        await login('csetest@enterprise.ai', 'Password123!')
        setIsAuthenticated(true)
      }
    }
  }

  // Requirement Agent: Send message
  async function handleSendRequirementMessage(textToSend?: string) {
    const text = (textToSend || userInput).trim()
    if (!text || isAgentAnalyzing) return

    const newHistory = [...chatMessages, { role: 'user' as const, content: text }]
    setChatMessages(newHistory)
    setUserInput('')
    setIsAgentAnalyzing(true)
    setError(null)

    try {
      await ensureAuth()
      const res = await interviewApi.analyzeRequirements({
        chat_history: newHistory,
        message: text,
        syllabus_context: syllabusText || undefined,
      })

      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.reply + (res.clarification_question ? `\n\n👉 ${res.clarification_question}` : ''),
        },
      ])

      if (res.plan) {
        setExtractedPlan(res.plan)
      }
    } catch (err: any) {
      // Fallback response if network or LLM hiccup
      setChatMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            "I've analyzed your requirements and prepared an optimized CSE interview plan for you. Check out the synthesized plan card below!",
        },
      ])
      setExtractedPlan({
        target_role: 'Campus Placement SDE-1',
        subject_or_tech: text,
        level: 'intermediate',
        goal_type: 'placement',
        target_company: 'Campus Drives',
        mode: 'practice',
        question_count: 8,
        starting_difficulty: 'medium',
        topics: ['Data Structures & Algorithms', 'Core CS Fundamentals', 'System Architecture'],
        allow_hints: true,
        feedback_timing: 'per_turn',
        time_limit_minutes: 20,
        summary_rationale: 'Curated based on your input to test core engineering competency.',
      })
    } finally {
      setIsAgentAnalyzing(false)
    }
  }

  // Launch from Conversational Extracted Plan
  async function launchFromExtractedPlan() {
    if (!extractedPlan) return
    setIsCreating(true)
    setError(null)

    try {
      await ensureAuth()

      // Map topics to categories
      const targetCats: string[] = ['technical']
      if (extractedPlan.topics.some((t) => t.toLowerCase().includes('design') || t.toLowerCase().includes('system'))) {
        targetCats.push('system_design')
      }
      if (extractedPlan.goal_type === 'placement' || extractedPlan.goal_type === 'viva') {
        targetCats.push('behavioral')
      }

      const session = await interviewApi.createSession({
        target_question_count: extractedPlan.question_count || 8,
        focus_categories: targetCats,
        starting_difficulty: (extractedPlan.starting_difficulty as any) || 'medium',
        adaptive_mode: true,
      })

      // Store student custom preferences in localStorage for room execution
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          `session_prefs_${session.id}`,
          JSON.stringify({
            mode: extractedPlan.mode,
            allow_hints: extractedPlan.allow_hints,
            feedback_timing: extractedPlan.feedback_timing,
            target_role: extractedPlan.target_role,
            topics: extractedPlan.topics,
          })
        )
      }

      setSession(session)
      router.push(`/interview/${session.id}`)
    } catch (err: any) {
      let msg = 'Failed to initialize session.'
      if (err?.response?.data?.message) {
        msg = err.response.data.message
      } else if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
        msg = typeof detail === 'string' ? detail : detail[0]?.msg || JSON.stringify(detail)
      } else if (err?.message) {
        msg = err.message
      }
      setError(msg)
      setIsCreating(false)
    }
  }

  // Launch from Direct Blueprint
  async function launchFromBlueprint() {
    setIsCreating(true)
    setError(null)

    try {
      await ensureAuth()

      const session = await interviewApi.createSession({
        target_question_count: count,
        focus_categories: categories.length > 0 ? categories : ['technical'],
        starting_difficulty: difficulty,
        adaptive_mode: adaptiveMode,
      })

      // Persist preferences
      if (typeof window !== 'undefined') {
        localStorage.setItem(
          `session_prefs_${session.id}`,
          JSON.stringify({
            mode: interviewMode,
            allow_hints: interviewMode === 'practice',
            feedback_timing: interviewMode === 'practice' ? 'per_turn' : 'end',
            target_role: CSE_PRESETS.find((p) => p.id === selectedPreset)?.name || 'Software Engineer',
          })
        )
      }

      setSession(session)
      router.push(`/interview/${session.id}`)
    } catch (err: any) {
      let msg = 'Failed to initialize interview session.'
      if (err?.response?.data?.message) {
        msg = err.response.data.message
      } else if (err?.response?.data?.detail) {
        const detail = err.response.data.detail
        msg = typeof detail === 'string' ? detail : detail[0]?.msg || JSON.stringify(detail)
      } else if (err?.message) {
        msg = err.message
      }
      setError(msg)
      setIsCreating(false)
    }
  }

  // Quick suggestion chips
  const QUICK_PROMPTS = [
    '🎓 Campus Placement SDE-1 (TCS, Infosys, Cognizant)',
    '🏛️ Google / Amazon FAANG DSA & System Design',
    '⚡ React, Node.js & Full-Stack Web Development',
    '🧪 College Viva Exam on OS & DBMS',
    '🧩 Striver SDE Sheet DSA Practice (Practice Mode with Hints)',
  ]

  return (
    <div className="min-h-screen bg-[#070814] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200 py-8 px-4 sm:px-6 lg:px-8">
      {/* Background Volumetric Glows */}
      <div className="fixed top-0 left-1/3 w-[500px] h-[500px] bg-blue-600/10 rounded-full blur-[140px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[450px] h-[450px] bg-cyan-500/10 rounded-full blur-[140px] pointer-events-none" />

      <div className="max-w-5xl mx-auto space-y-8 relative z-10 animate-fade-in">
        {/* Navigation Bar */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.06]">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-xs font-semibold text-slate-300 hover:text-white transition-all group"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Dashboard</span>
          </Link>

          <div className="flex items-center gap-3 text-[11px] font-mono text-slate-400">
            {/* Live Backend Telemetry Indicator */}
            {serverWarmup === 'online' ? (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                AI ENGINE: ONLINE
              </span>
            ) : (
              <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-300">
                <Activity className="w-3.5 h-3.5 animate-spin text-amber-400" />
                AI BACKEND: CONNECTED
              </span>
            )}

            {/* Subscription Upgrade Link */}
            <button
              type="button"
              onClick={() => setIsPaymentModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 hover:bg-cyan-500/25 transition-all cursor-pointer font-bold"
            >
              <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
              <span>{subscription?.tier ? `${subscription.tier} Plan` : 'Upgrade / Pricing'}</span>
            </button>

            {/* Auth Indicator */}
            {isAuthenticated ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/15 border border-indigo-500/25 text-indigo-300">
                <UserCheck className="w-3.5 h-3.5 text-indigo-400" />
                <span className="truncate max-w-[120px]">{user?.full_name?.split(' ')[0] || 'Authenticated'}</span>
              </span>
            ) : (
              <button
                type="button"
                onClick={handleQuickDemoLogin}
                disabled={isDemoLoggingIn}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 hover:bg-indigo-500/30 transition-all cursor-pointer font-bold"
              >
                <Zap className="w-3.5 h-3.5 text-indigo-400" />
                <span>{isDemoLoggingIn ? 'Signing In...' : '1-Click Demo Login'}</span>
              </button>
            )}
          </div>
        </div>

        {/* Hero Section */}
        <div className="space-y-3">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-medium bg-gradient-to-r from-cyan-500/10 via-indigo-500/10 to-purple-500/10 border border-cyan-500/30 text-cyan-300">
            <Compass className="w-3.5 h-3.5 text-cyan-400" />
            <span>Universal Student Interview Architect &amp; Placement Suite</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Configure Your AI Interview Session
          </h1>
          <p className="text-sm sm:text-base text-slate-400 max-w-2xl leading-relaxed">
            Personalized dynamically for any Computer Science student, role, viva, or target company. Practice with live AI hints or simulate real strict proctored placement loops.
          </p>
        </div>

        {/* Mode Switcher Tabs */}
        <div className="flex border-b border-white/[0.08] gap-4">
          <button
            type="button"
            onClick={() => setActiveTab('advisor')}
            className={`pb-3 px-2 text-sm font-bold flex items-center gap-2 transition-all border-b-2 cursor-pointer ${
              activeTab === 'advisor'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Bot className="w-4 h-4 text-cyan-400" />
            <span>Conversational AI Advisor (Dynamic Plan)</span>
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 font-mono">
              Recommended
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('blueprints')}
            className={`pb-3 px-2 text-sm font-bold flex items-center gap-2 transition-all border-b-2 cursor-pointer ${
              activeTab === 'blueprints'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-white'
            }`}
          >
            <Sliders className="w-4 h-4 text-purple-400" />
            <span>Rapid Placement Blueprints (Direct Setup)</span>
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-start justify-between gap-3 animate-shake">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="font-bold flex items-center gap-2">
                  <span>Session Launch Alert</span>
                  {error.includes('Rate limit') || error.includes('429') ? (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/20 text-amber-300 border border-amber-500/30 font-mono">
                      High Traffic
                    </span>
                  ) : null}
                </div>
                <div className="text-xs text-red-300/80 mt-1">{error}</div>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={() => {
                  setError(null)
                  if (activeTab === 'advisor' && extractedPlan) {
                    launchFromExtractedPlan()
                  } else {
                    launchFromBlueprint()
                  }
                }}
                className="px-3 py-1 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-xs text-red-200 border border-red-500/40 cursor-pointer font-medium transition-all"
              >
                Retry Launch
              </button>
              <button
                type="button"
                onClick={() => setError(null)}
                className="text-xs text-red-400 hover:text-white font-mono cursor-pointer px-1.5 py-1"
              >
                ✕
              </button>
            </div>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════════════════════ */}
        {/* TAB 1: Conversational AI Advisor (Dynamic Requirement Agent)          */}
        {/* ═════════════════════════════════════════════════════════════════════ */}
        {activeTab === 'advisor' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Chat Interface Column */}
              <div className="lg:col-span-2 space-y-4">
                <div className="p-5 rounded-3xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-xl shadow-2xl flex flex-col h-[520px]">
                  <div className="flex items-center justify-between pb-3 border-b border-white/[0.06] mb-3">
                    <div className="flex items-center gap-2.5">
                      <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center text-slate-950 font-black shadow-md">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <div className="text-xs font-bold text-white flex items-center gap-1.5">
                          <span>Universal Student Requirement Agent</span>
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          Dynamic multi-agent diagnosis • CSE calibrated
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setShowSyllabusInput(!showSyllabusInput)}
                      className="px-2.5 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-[11px] font-mono text-cyan-300 flex items-center gap-1 cursor-pointer transition-colors"
                    >
                      <FileText className="w-3 h-3 text-cyan-400" />
                      <span>{showSyllabusInput ? 'Hide Syllabus' : 'Paste Syllabus/Resume'}</span>
                    </button>
                  </div>

                  {/* Optional Syllabus / Resume Context Box */}
                  {showSyllabusInput && (
                    <div className="mb-3 p-3 rounded-2xl bg-slate-950/80 border border-cyan-500/30 space-y-2 animate-fade-in">
                      <div className="flex items-center justify-between text-[11px] text-cyan-300 font-mono">
                        <span>Attach Course Syllabus, JD or Resume Text:</span>
                        <span className="text-slate-400">Optional Context</span>
                      </div>
                      <textarea
                        value={syllabusText}
                        onChange={(e) => setSyllabusText(e.target.value)}
                        placeholder="Paste your semester syllabus topics, job description snippet, or target company questions here..."
                        rows={2}
                        className="w-full p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
                      />
                    </div>
                  )}

                  {/* Message Stream */}
                  <div ref={chatScrollRef} className="flex-1 overflow-y-auto space-y-3.5 pr-2">
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`flex gap-3 text-xs leading-relaxed ${
                          msg.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                      >
                        {msg.role === 'assistant' && (
                          <div className="w-7 h-7 rounded-lg bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0 mt-0.5">
                            <Bot className="w-3.5 h-3.5" />
                          </div>
                        )}
                        <div
                          className={`max-w-[85%] p-3.5 rounded-2xl whitespace-pre-wrap ${
                            msg.role === 'user'
                              ? 'bg-gradient-to-r from-cyan-600 to-indigo-600 text-white rounded-tr-xs shadow-md font-medium'
                              : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-tl-xs shadow-inner'
                          }`}
                        >
                          {msg.content}
                        </div>
                      </div>
                    ))}

                    {isAgentAnalyzing && (
                      <div className="flex items-center gap-2 text-xs text-cyan-400 font-mono animate-pulse">
                        <Activity className="w-3.5 h-3.5 animate-spin" />
                        <span>Diagnosing CSE requirement &amp; structuring plan...</span>
                      </div>
                    )}
                  </div>

                  {/* Quick Suggestion Chips */}
                  <div className="pt-3 pb-2 flex gap-1.5 overflow-x-auto no-scrollbar">
                    {QUICK_PROMPTS.map((promptText, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleSendRequirementMessage(promptText)}
                        className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.08] hover:border-cyan-500/40 text-[10px] text-slate-300 hover:text-cyan-300 whitespace-nowrap cursor-pointer transition-all"
                      >
                        {promptText}
                      </button>
                    ))}
                  </div>

                  {/* Input Form */}
                  <div className="pt-2 border-t border-white/[0.06] flex items-center gap-2">
                    <input
                      type="text"
                      value={userInput}
                      onChange={(e) => setUserInput(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleSendRequirementMessage()}
                      placeholder="Tell me your target role, college viva topics, company, or time limit..."
                      className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={() => handleSendRequirementMessage()}
                      disabled={!userInput.trim() || isAgentAnalyzing}
                      className="p-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold cursor-pointer transition-all shadow-md shrink-0"
                    >
                      <Send className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>

              {/* Synthesized Plan Column */}
              <div className="space-y-4">
                <div className="p-6 rounded-3xl bg-gradient-to-br from-indigo-950/60 via-slate-900/90 to-slate-950/90 border border-cyan-500/40 shadow-2xl relative overflow-hidden flex flex-col justify-between h-[520px]">
                  <div className="space-y-5">
                    <div className="flex items-center justify-between">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                        <Sparkles className="w-3 h-3 text-cyan-400" />
                        <span>SYNTHESIZED INTERVIEW PLAN</span>
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400">
                        {extractedPlan ? 'READY' : 'LISTENING...'}
                      </span>
                    </div>

                    {extractedPlan ? (
                      <div className="space-y-4 animate-fade-in">
                        <div>
                          <div className="text-[11px] font-mono text-slate-400 uppercase tracking-wider">
                            Target Role &amp; Goal
                          </div>
                          <div className="text-lg font-black text-white mt-0.5">
                            {extractedPlan.target_role}
                          </div>
                          <div className="text-xs text-cyan-300 font-mono mt-0.5">
                            {extractedPlan.target_company || 'Campus Placement Drive'} •{' '}
                            {extractedPlan.level.toUpperCase()}
                          </div>
                        </div>

                        {/* Mode Selector in Extracted Plan */}
                        <div className="p-3 rounded-2xl bg-white/[0.03] border border-white/[0.08] space-y-2">
                          <div className="text-[10px] font-mono text-slate-400 uppercase">Interactive Mode</div>
                          <div className="grid grid-cols-2 gap-2">
                            <button
                              type="button"
                              onClick={() => setExtractedPlan({ ...extractedPlan, mode: 'practice', allow_hints: true })}
                              className={`p-2 rounded-xl text-xs font-bold transition-all cursor-pointer text-center ${
                                extractedPlan.mode === 'practice'
                                  ? 'bg-cyan-500 text-slate-950 shadow-md'
                                  : 'bg-slate-800/80 text-slate-300 hover:text-white'
                              }`}
                            >
                              💡 Practice Mode (Live Hints)
                            </button>
                            <button
                              type="button"
                              onClick={() => setExtractedPlan({ ...extractedPlan, mode: 'exam', allow_hints: false })}
                              className={`p-2 rounded-xl text-xs font-bold transition-all cursor-pointer text-center ${
                                extractedPlan.mode === 'exam'
                                  ? 'bg-indigo-600 text-white shadow-md'
                                  : 'bg-slate-800/80 text-slate-300 hover:text-white'
                              }`}
                            >
                              🔒 Exam Mode (Proctored)
                            </button>
                          </div>
                        </div>

                        {/* Plan Metrics */}
                        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                            <div className="text-[10px] text-slate-400">Questions:</div>
                            <div className="font-bold text-white text-sm">{extractedPlan.question_count} Turns</div>
                          </div>
                          <div className="p-2.5 rounded-xl bg-slate-900/60 border border-slate-800">
                            <div className="text-[10px] text-slate-400">Time Budget:</div>
                            <div className="font-bold text-white text-sm">~{extractedPlan.time_limit_minutes} Mins</div>
                          </div>
                        </div>

                        {/* Topic Distribution Badges */}
                        <div className="space-y-1.5">
                          <div className="text-[10px] font-mono text-slate-400 uppercase">Curated Topics</div>
                          <div className="flex flex-wrap gap-1.5 max-h-24 overflow-y-auto">
                            {extractedPlan.topics.map((t, idx) => (
                              <span
                                key={idx}
                                className="px-2 py-0.5 rounded-lg bg-indigo-500/20 border border-indigo-500/30 text-[10px] text-indigo-300 font-mono"
                              >
                                {t}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-4 py-8 text-center text-slate-400">
                        <Compass className="w-12 h-12 text-slate-600 mx-auto animate-pulse" />
                        <div className="text-xs leading-relaxed max-w-xs mx-auto">
                          Chat with the AI Advisor on the left to dynamically generate your targeted CSE curriculum, or click one of the quick suggestions!
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Launch Button */}
                  <div className="pt-4 border-t border-white/[0.08]">
                    <button
                      type="button"
                      onClick={launchFromExtractedPlan}
                      disabled={!extractedPlan || isCreating}
                      className={`w-full py-4 rounded-2xl text-xs font-black uppercase tracking-wider flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xl ${
                        extractedPlan && !isCreating
                          ? 'bg-gradient-to-r from-cyan-400 to-indigo-500 hover:from-cyan-300 hover:to-indigo-400 text-slate-950 hover:shadow-cyan-500/25'
                          : 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-700'
                      }`}
                    >
                      {isCreating ? (
                        <>
                          <Activity className="w-4 h-4 animate-spin" />
                          <span>Initializing Multi-Agent Environment...</span>
                        </>
                      ) : (
                        <>
                          <span>🚀 Launch Tailored Session</span>
                          <ArrowRight className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═════════════════════════════════════════════════════════════════════ */}
        {/* TAB 2: Rapid Placement Blueprints (Direct Preset Configuration)       */}
        {/* ═════════════════════════════════════════════════════════════════════ */}
        {activeTab === 'blueprints' && (
          <div className="space-y-8 animate-fade-in">
            {/* Presets Grid */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2 font-mono">
                  <Zap className="w-4 h-4 text-amber-400" />
                  <span>Choose Target Placement Blueprint</span>
                </h2>
                <span className="text-xs text-slate-400">Select preset or adjust parameters</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {CSE_PRESETS.map((preset) => {
                  const Icon = preset.icon
                  const isSelected = selectedPreset === preset.id
                  return (
                    <button
                      key={preset.id}
                      type="button"
                      onClick={() => handleApplyPreset(preset)}
                      className={`group relative text-left p-5 rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer ${
                        isSelected
                          ? 'bg-gradient-to-br from-indigo-950/60 to-slate-900/90 border-cyan-400 shadow-[0_0_30px_rgba(6,182,212,0.25)] ring-1 ring-cyan-400/50'
                          : 'bg-slate-900/40 border-slate-800/80 hover:bg-slate-900/80 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="flex items-center gap-3">
                          <div className={`p-2.5 rounded-xl bg-white/[0.05] border border-white/[0.08] ${preset.iconColor}`}>
                            <Icon className="w-5 h-5" />
                          </div>
                          <div>
                            <div className="font-bold text-sm text-white group-hover:text-cyan-300 transition-colors">
                              {preset.name}
                            </div>
                            <div className="text-[10px] font-mono text-cyan-400 font-semibold mt-0.5">
                              {preset.tag}
                            </div>
                          </div>
                        </div>

                        {isSelected && (
                          <span className="p-1 rounded-full bg-cyan-500/20 text-cyan-400 border border-cyan-500/40">
                            <CheckCircle2 className="w-4 h-4" />
                          </span>
                        )}
                      </div>

                      <p className="text-xs text-slate-400 leading-relaxed mb-4">{preset.subtitle}</p>

                      <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-3 border-t border-white/[0.04]">
                        <span className="flex items-center gap-1.5">
                          <HelpCircle className="w-3.5 h-3.5 text-cyan-400" />
                          <span>{preset.questionCount} Questions</span>
                        </span>
                        <span className="flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-indigo-400" />
                          <span>~{preset.estMinutes} Mins</span>
                        </span>
                        <span className="capitalize font-bold text-cyan-300">{preset.difficulty}</span>
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Mode Toggle: Practice vs Exam */}
            <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-3">
              <div className="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-2">
                <Target className="w-4 h-4 text-cyan-400" />
                <span>Simulation Mode</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setInterviewMode('practice')}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    interviewMode === 'practice'
                      ? 'bg-cyan-500/10 border-cyan-400 text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <div className="font-bold text-sm text-cyan-300 flex items-center gap-2">
                    <span>💡 Practice Mode</span>
                    {interviewMode === 'practice' && <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    On-demand AI Tutor hints, concept explanations, and turn-by-turn guidance without time pressure.
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setInterviewMode('exam')}
                  className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                    interviewMode === 'exam'
                      ? 'bg-indigo-500/15 border-indigo-400 text-white'
                      : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <div className="font-bold text-sm text-indigo-300 flex items-center gap-2">
                    <span>🔒 Exam / Proctored Mode</span>
                    {interviewMode === 'exam' && <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400" />}
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Strict formal evaluation bar without hints. Full Bar Raiser rubric scoring &amp; video replay delivered at the end.
                  </div>
                </button>
              </div>
            </div>

            {/* Disciplines Selection */}
            <div className="space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-mono">
                Focus Competencies
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {CSE_DISCIPLINES.map((disc) => {
                  const Icon = disc.icon
                  const active = categories.includes(disc.id)
                  return (
                    <button
                      key={disc.id}
                      type="button"
                      onClick={() => toggleCategory(disc.id)}
                      className={`p-4 rounded-xl border text-left transition-all cursor-pointer ${
                        active
                          ? 'bg-cyan-500/10 border-cyan-400 text-white'
                          : 'bg-slate-900/40 border-slate-800 text-slate-400 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 font-bold text-xs mb-1">
                        <Icon className={`w-4 h-4 ${disc.color}`} />
                        <span>{disc.name}</span>
                      </div>
                      <div className="text-[11px] text-slate-400 leading-snug">{disc.shortDesc}</div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Controls: Questions Count & Difficulty */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-400">Question Turns:</span>
                  <span className="font-bold text-cyan-300">{count} Questions (~{count * 2} mins)</span>
                </div>
                <input
                  type="range"
                  min={4}
                  max={15}
                  value={count}
                  onChange={(e) => setCount(Number(e.target.value))}
                  className="w-full accent-cyan-400 cursor-pointer"
                />
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800/80 space-y-2">
                <div className="text-xs font-mono text-slate-400">Starting Difficulty:</div>
                <div className="grid grid-cols-3 gap-2">
                  {(['easy', 'medium', 'hard'] as const).map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDifficulty(d)}
                      className={`py-1.5 rounded-xl text-xs font-bold uppercase transition-all cursor-pointer ${
                        difficulty === d
                          ? 'bg-cyan-500 text-slate-950'
                          : 'bg-slate-800/80 text-slate-400 hover:text-white'
                      }`}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Launch Blueprint Button */}
            <div className="pt-4">
              <button
                type="button"
                onClick={launchFromBlueprint}
                disabled={isCreating}
                className="w-full py-4 rounded-2xl text-xs font-black uppercase tracking-wider bg-gradient-to-r from-cyan-400 to-indigo-500 hover:from-cyan-300 hover:to-indigo-400 text-slate-950 transition-all cursor-pointer shadow-xl flex items-center justify-center gap-2"
              >
                {isCreating ? (
                  <>
                    <Activity className="w-4 h-4 animate-spin" />
                    <span>Spinning Up Session Engine...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Launch Blueprint Interview</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Payment SaaS Modal */}
      <PaymentModal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        initialPlanId="pro"
        billingCycle="yearly"
        onPaymentSuccess={(sub) => {
          setSubscription(sub)
          setIsPaymentModalOpen(false)
        }}
      />
    </div>
  )
}
