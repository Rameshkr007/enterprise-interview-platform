'use client'
import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'

export default function DashboardPage() {
  const { user, fetchMe, logout } = useAuthStore()
  const router = useRouter()

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().user) router.push('/login')
    })
  }, [fetchMe, router])

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="skeleton w-32 h-8" />
      </div>
    )
  }

  const actions = [
    { href: '/ats',           icon: '📊', title: 'ATS Analyzer',           desc: 'Semantic vector scoring of your resume against any job description.',     cta: 'Run Analysis',       color: '#6366f1' },
    { href: '/interview/new', icon: '🎤', title: 'Mock Interview',         desc: 'Adaptive AI interview with 3D avatar, computer vision and LangGraph.',     cta: 'Start Interview',    color: '#8b5cf6' },
    { href: '/coding',        icon: '💻', title: 'Coding Round',           desc: 'AI-generated challenges with complexity analysis and bug detection.',       cta: 'Start Coding',       color: '#06b6d4' },
    { href: '/company-mode',  icon: '🏢', title: 'Company Mode',           desc: 'Practice Google, Amazon, Meta, Microsoft interviews with LP scoring.',     cta: 'Pick Company',       color: '#f59e0b' },
    { href: '/negotiation',   icon: '💰', title: 'Salary Negotiation',     desc: 'Simulate high-stakes recruiter counter-offers and maximize compensation.',cta: 'Spar with HR',      color: '#10b981' },
    { href: '/resume-builder',icon: '✨', title: 'AI Career Intelligence', desc: 'Resume rewriting, career roadmap, salary benchmarks and coaching.',        cta: 'Optimize Resume',    color: '#ec4899' },
    { href: '/job-tracker',   icon: '💼', title: 'Job Tracker',            desc: 'Kanban board for all your applications — from wishlist to offer.',         cta: 'Track Jobs',         color: '#f97316' },
    { href: '/daily-challenge',icon:'🔥', title: 'Daily Challenge',        desc: 'One question per day with XP, streaks, and SM-2 spaced repetition.',      cta: 'Take Challenge',     color: '#ef4444' },
    { href: '/analytics',     icon: '📈', title: 'Analytics & Ranking',    desc: 'Score trends, skill heatmap, badges, streaks and global leaderboard.',     cta: 'View Analytics',     color: '#a855f7' },
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-white/5 px-8 py-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <span className="text-white text-xs font-bold">AI</span>
          </div>
          <span className="font-bold text-white">InterviewAI</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-slate-400 text-sm">{user.full_name}</span>
          <button
            id="logout-btn"
            onClick={() => { logout(); router.push('/login') }}
            className="btn-ghost text-sm py-2 px-4"
          >
            Sign Out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-8 py-16 animate-fade-in">
        <div className="mb-12">
          <h1 className="text-3xl font-bold text-white mb-2">
            Welcome back, <span className="gradient-text">{user.full_name.split(' ')[0]}</span>
          </h1>
          <p className="text-slate-400">What would you like to work on today?</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {actions.map((a) => (
            <div key={a.href} className="glass-card p-8 flex flex-col gap-4">
              <div className="text-4xl" dangerouslySetInnerHTML={{ __html: a.icon }} />
              <div>
                <h2 className="text-xl font-bold text-white mb-2">{a.title}</h2>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">{a.desc}</p>
              </div>
              <Link href={a.href} className="btn-primary self-start">{a.cta}</Link>
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}
