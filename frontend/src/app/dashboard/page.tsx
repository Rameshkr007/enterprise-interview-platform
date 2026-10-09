'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import HolographicBrain from '@/components/3d/HolographicBrain'
import {
  LayoutDashboard,
  Bot,
  Sparkles,
  Code2,
  Cpu,
  Building2,
  Coins,
  FileText,
  Briefcase,
  Flame,
  BarChart3,
  Settings,
  HelpCircle,
  Bell,
  Moon,
  Search,
  Plus,
  CheckCircle2,
  ChevronRight,
  Zap,
  TrendingUp,
  Users,
  Check,
  DollarSign,
  ArrowUpRight,
  ShieldCheck,
  Mic,
  PenTool,
  Layers,
  LogOut,
  Sliders,
} from 'lucide-react'

export default function DashboardPage() {
  const { user, fetchMe, logout } = useAuthStore()
  const router = useRouter()
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly')
  const [searchQuery, setSearchQuery] = useState('')

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().user) {
        router.push('/login')
      }
    })
  }, [fetchMe, router])

  if (!user) {
    return (
      <div className="min-h-screen bg-[#080913] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 rounded-2xl border-2 border-indigo-500/30 border-t-indigo-500 animate-spin" />
          <p className="font-mono text-xs text-slate-400 tracking-wider">LOADING AI COMMAND CENTER...</p>
        </div>
      </div>
    )
  }

  const firstName = user.full_name?.split(' ')[0] || 'Alex'

  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard', active: true },
    { name: 'AI Mock Interview', icon: Mic, href: '/interview/new' },
    { name: 'ATS Resume Analyzer', icon: FileText, href: '/ats' },
    { name: 'AI Coding Studio', icon: Code2, href: '/coding' },
    { name: 'System Design', icon: Cpu, href: '/system-design' },
    { name: 'Company Mode', icon: Building2, href: '/company-mode' },
    { name: 'Salary Negotiation', icon: Coins, href: '/negotiation' },
    { name: 'Career Intelligence', icon: Sparkles, href: '/resume-builder' },
    { name: 'Job Tracker', icon: Briefcase, href: '/job-tracker' },
    { name: 'Daily Challenge', icon: Flame, href: '/daily-challenge' },
    { name: 'Data & Analytics', icon: BarChart3, href: '/analytics' },
    { name: 'Settings & Telemetry', icon: Settings, href: '/admin/diagnostics' },
    { name: 'Support Center', icon: HelpCircle, href: '#support' },
  ]

  return (
    <div className="min-h-screen bg-[#070814] text-slate-100 flex flex-col md:flex-row antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* ── 1. LEFT SIDEBAR (Matching Reference UI) ────────────────────────── */}
      <aside className="w-full md:w-64 bg-[#0a0c1a] border-r border-white/[0.06] flex flex-col justify-between p-4 shrink-0 z-30">
        <div>
          {/* Brand Logo Header */}
          <div className="flex items-center gap-3 px-2 py-4 mb-4">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)]">
              <span className="text-white font-black text-lg tracking-wider">N</span>
            </div>
            <div>
              <div className="font-extrabold text-base tracking-wide text-white flex items-center gap-1.5">
                INTERVIEW AI
              </div>
              <div className="text-[11px] font-mono text-slate-400">AI Career Platform</div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                    item.active
                      ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-[0_4px_20px_rgba(99,102,241,0.35)]'
                      : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-4 h-4" />
                    <span>{item.name}</span>
                  </div>
                  {!item.active && <ChevronRight className="w-3.5 h-3.5 opacity-40" />}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Upgrade to Pro Card at bottom of sidebar */}
        <div className="mt-8 pt-4">
          <div className="relative rounded-2xl p-4 bg-gradient-to-br from-[#121630] to-[#181a38] border border-indigo-500/20 text-center overflow-hidden">
            <div className="w-12 h-12 mx-auto rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center mb-3 shadow-[0_0_20px_rgba(99,102,241,0.25)]">
              <Sparkles className="w-6 h-6 text-indigo-400 animate-pulse" />
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Upgrade to Pro</h4>
            <p className="text-[11px] text-slate-400 mb-3 leading-relaxed">
              Unlock unlimited LangGraph adaptive simulations and 1536d vector scans.
            </p>
            <Link
              href="#pricing"
              className="block w-full py-2 px-3 rounded-lg bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-xs font-bold text-white shadow-md hover:brightness-110 transition-all"
            >
              Upgrade Now
            </Link>
          </div>
        </div>
      </aside>

      {/* ── MAIN CONTENT AREA ──────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Header Bar */}
        <header className="h-18 px-6 py-4 border-b border-white/[0.06] bg-[#080914]/80 backdrop-blur-xl flex items-center justify-between gap-4 sticky top-0 z-20">
          {/* Search Input with ⌘ K */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search interviews, questions, skills..."
              className="w-full pl-10 pr-14 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-xs text-white placeholder-slate-400 focus:outline-none focus:border-indigo-500/60 focus:bg-white/[0.06] transition-all"
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 text-[10px] font-mono text-slate-400 bg-white/[0.08] px-1.5 py-0.5 rounded border border-white/10">
              ⌘ K
            </kbd>
          </div>

          {/* Right Action Icons & User Profile */}
          <div className="flex items-center gap-4">
            <button className="relative p-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-slate-300 hover:text-white transition-colors">
              <Bell className="w-4 h-4" />
              <span className="w-2 h-2 rounded-full bg-indigo-500 absolute top-1.5 right-1.5 animate-pulse" />
            </button>

            <button className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-slate-300 hover:text-white transition-colors">
              <Moon className="w-4 h-4" />
            </button>

            <div className="flex items-center gap-3 pl-3 border-l border-white/[0.08]">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 flex items-center justify-center font-bold text-sm text-white shadow-md">
                {firstName.charAt(0)}
              </div>
              <div className="text-left hidden sm:block">
                <div className="text-xs font-bold text-white leading-tight">{user.full_name}</div>
                <div className="text-[10px] font-mono text-indigo-400 leading-tight">Pro Candidate</div>
              </div>
              <button
                onClick={() => {
                  logout()
                  router.push('/login')
                }}
                title="Sign Out"
                className="p-1.5 rounded-lg text-slate-400 hover:text-red-400 hover:bg-white/[0.05] transition-colors ml-1"
              >
                <LogOut className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </header>

        {/* Dashboard Grid Container */}
        <main className="p-6 md:p-8 space-y-8">
          {/* ── TOP SECTION: HERO BANNER & RIGHT-HAND CARDS ────────────────── */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
            {/* Left 8 Columns: Hero Card + Stats + Charts */}
            <div className="lg:col-span-8 space-y-6">
              {/* 1. Hero Banner with 3D Holographic Brain */}
              <div className="relative rounded-3xl bg-gradient-to-r from-[#0e122b] via-[#141838] to-[#121633] border border-indigo-500/25 p-7 sm:p-8 overflow-hidden shadow-[0_10px_40px_rgba(0,0,0,0.5)] flex flex-col sm:flex-row items-center justify-between gap-6">
                {/* Background Ambient Glow */}
                <div className="absolute top-0 right-1/4 w-72 h-72 bg-purple-600/15 rounded-full blur-3xl pointer-events-none" />

                <div className="relative z-10 max-w-md space-y-3">
                  <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug">
                    The Future of Hiring is <br />
                    Automated with <span className="bg-gradient-to-r from-blue-400 via-indigo-300 to-purple-400 bg-clip-text text-transparent">AI</span>
                  </h1>
                  <p className="text-xs sm:text-sm text-slate-400 leading-relaxed font-normal">
                    Simulate, automate and scale your technical career readiness using the power of generative AI and biometric telemetry.
                  </p>
                  <div className="pt-2">
                    <Link
                      href="/interview/new"
                      className="inline-flex items-center gap-2 py-3 px-6 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-xs sm:text-sm font-bold text-white shadow-[0_0_25px_rgba(99,102,241,0.4)] hover:brightness-110 transition-all"
                    >
                      <Zap className="w-4 h-4 fill-white" />
                      <span>Create New Simulation</span>
                    </Link>
                  </div>
                </div>

                {/* 3D Holographic Brain on Right */}
                <div className="relative w-full sm:w-64 h-56 shrink-0 flex items-center justify-center">
                  <HolographicBrain />
                </div>
              </div>

              {/* 2. Four Metric Stats Cards */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-medium text-slate-400">Simulations</span>
                    <div className="w-7 h-7 rounded-lg bg-indigo-500/15 flex items-center justify-center text-indigo-400">
                      <Zap className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">142</div>
                  <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 mt-1">
                    <span>↑ 28%</span> <span className="text-slate-400">vs last month</span>
                  </div>
                </div>

                <div className="rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-medium text-slate-400">Skills Verified</span>
                    <div className="w-7 h-7 rounded-lg bg-blue-500/15 flex items-center justify-center text-blue-400">
                      <Users className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">2,458</div>
                  <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 mt-1">
                    <span>↑ 34%</span> <span className="text-slate-400">vs last month</span>
                  </div>
                </div>

                <div className="rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-medium text-slate-400">Turns Scored</span>
                    <div className="w-7 h-7 rounded-lg bg-purple-500/15 flex items-center justify-center text-purple-400">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">8,642</div>
                  <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 mt-1">
                    <span>↑ 19%</span> <span className="text-slate-400">vs last month</span>
                  </div>
                </div>

                <div className="rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[11px] font-medium text-slate-400">Comp Impact</span>
                    <div className="w-7 h-7 rounded-lg bg-emerald-500/15 flex items-center justify-center text-emerald-400">
                      <DollarSign className="w-3.5 h-3.5" />
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-white font-mono">$40,980</div>
                  <div className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 mt-1">
                    <span>↑ 42%</span> <span className="text-slate-400">vs last month</span>
                  </div>
                </div>
              </div>

              {/* 3. Performance Chart & AI Activity Overview Donut */}
              <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                {/* Performance Trend Chart (7 cols) */}
                <div className="md:col-span-7 rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-xs font-bold text-white">Interview Performance</h3>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Success Rate <span className="font-bold text-emerald-400 font-mono">94.6%</span>{' '}
                        <span className="text-[10px] text-emerald-400">↑ 18.2%</span>
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-slate-400 px-2 py-1 rounded-lg bg-white/[0.04] border border-white/[0.08]">
                      This Month ▾
                    </span>
                  </div>

                  {/* SVG Area Chart */}
                  <div className="h-44 w-full relative">
                    <svg viewBox="0 0 320 120" className="w-full h-full overflow-visible">
                      <defs>
                        <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.45" />
                          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0" />
                        </linearGradient>
                      </defs>
                      {/* Grid Lines */}
                      <line x1="0" y1="30" x2="320" y2="30" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                      <line x1="0" y1="65" x2="320" y2="65" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />
                      <line x1="0" y1="100" x2="320" y2="100" stroke="rgba(255,255,255,0.05)" strokeDasharray="3 3" />

                      {/* Area Fill */}
                      <path
                        d="M 10 95 Q 45 92 70 80 T 130 65 T 190 75 T 250 40 T 310 25 L 310 115 L 10 115 Z"
                        fill="url(#chartGradient)"
                      />
                      {/* Line Stroke */}
                      <path
                        d="M 10 95 Q 45 92 70 80 T 130 65 T 190 75 T 250 40 T 310 25"
                        fill="none"
                        stroke="#a855f7"
                        strokeWidth="2.5"
                        strokeLinecap="round"
                      />
                      {/* Data Point Nodes */}
                      {[
                        { cx: 10, cy: 95 },
                        { cx: 70, cy: 80 },
                        { cx: 130, cy: 65 },
                        { cx: 190, cy: 75 },
                        { cx: 250, cy: 40 },
                        { cx: 310, cy: 25 },
                      ].map((p, i) => (
                        <circle
                          key={i}
                          cx={p.cx}
                          cy={p.cy}
                          r={i === 5 ? '4' : '3'}
                          fill={i === 5 ? '#00f0ff' : '#c084fc'}
                          stroke="#080914"
                          strokeWidth="2"
                        />
                      ))}
                    </svg>
                    <div className="flex justify-between text-[10px] font-mono text-slate-400 mt-1 px-2">
                      <span>May 1</span>
                      <span>May 15</span>
                      <span>May 31</span>
                    </div>
                  </div>
                </div>

                {/* AI Activity Overview Donut Chart (5 cols) */}
                <div className="md:col-span-5 rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                  <h3 className="text-xs font-bold text-white mb-3">AI Activity Overview</h3>

                  <div className="flex items-center gap-4">
                    {/* SVG Donut */}
                    <div className="relative w-28 h-28 shrink-0 flex items-center justify-center">
                      <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                        <circle cx="50" cy="50" r="38" fill="none" stroke="#161b33" strokeWidth="14" />
                        {/* Segment 1: System Design (35%) */}
                        <circle
                          cx="50"
                          cy="50"
                          r="38"
                          fill="none"
                          stroke="#8b5cf6"
                          strokeWidth="14"
                          strokeDasharray="83.5 238"
                          strokeDashoffset="0"
                        />
                        {/* Segment 2: Distributed Systems (25%) */}
                        <circle
                          cx="50"
                          cy="50"
                          r="38"
                          fill="none"
                          stroke="#3b82f6"
                          strokeWidth="14"
                          strokeDasharray="59.6 238"
                          strokeDashoffset="-83.5"
                        />
                        {/* Segment 3: Coding (20%) */}
                        <circle
                          cx="50"
                          cy="50"
                          r="38"
                          fill="none"
                          stroke="#06b6d4"
                          strokeWidth="14"
                          strokeDasharray="47.7 238"
                          strokeDashoffset="-143.1"
                        />
                        {/* Segment 4: Behavioral (10%) */}
                        <circle
                          cx="50"
                          cy="50"
                          r="38"
                          fill="none"
                          stroke="#f97316"
                          strokeWidth="14"
                          strokeDasharray="23.8 238"
                          strokeDashoffset="-190.8"
                        />
                      </svg>
                      <div className="absolute text-center">
                        <div className="text-[10px] text-slate-400 font-mono">Total</div>
                        <div className="text-xs font-bold text-white font-mono">12,749</div>
                      </div>
                    </div>

                    {/* Donut Legend */}
                    <div className="space-y-1.5 text-[11px] font-mono flex-1">
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-purple-500" /> System Design
                        </span>
                        <span className="text-white font-semibold">35%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-blue-500" /> Cloud & Arch
                        </span>
                        <span className="text-white font-semibold">25%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-cyan-500" /> Algorithms
                        </span>
                        <span className="text-white font-semibold">20%</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="flex items-center gap-1.5 text-slate-300">
                          <span className="w-2 h-2 rounded-full bg-orange-500" /> Behavioral
                        </span>
                        <span className="text-white font-semibold">10%</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* 4. Automation Modules Row */}
              <div>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider">Simulation Modules</h3>
                  <Link href="/analytics" className="text-[11px] font-mono text-indigo-400 hover:underline">
                    View All Modules &gt;
                  </Link>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  {[
                    {
                      name: 'AI Mock Interview',
                      desc: 'Adaptive multi-turn interview with biometric scoring.',
                      icon: Mic,
                      href: '/interview/new',
                    },
                    {
                      name: 'Smart ATS Analyzer',
                      desc: '1536d vector cosine match with skill gap extraction.',
                      icon: FileText,
                      href: '/ats',
                    },
                    {
                      name: 'AI Coding Studio',
                      desc: 'In-browser challenges with algorithmic validation.',
                      icon: Code2,
                      href: '/coding',
                    },
                    {
                      name: 'System Design Board',
                      desc: 'High-scale architecture design and tradeoff rubrics.',
                      icon: Cpu,
                      href: '/system-design',
                    },
                  ].map((m) => {
                    const Icon = m.icon
                    return (
                      <div
                        key={m.name}
                        className="rounded-2xl p-4 bg-[#0d1024] border border-white/[0.06] hover:border-indigo-500/40 transition-all flex flex-col justify-between"
                      >
                        <div>
                          <div className="w-8 h-8 rounded-xl bg-indigo-500/15 flex items-center justify-center text-indigo-400 mb-3">
                            <Icon className="w-4 h-4" />
                          </div>
                          <h4 className="text-xs font-bold text-white mb-1">{m.name}</h4>
                          <p className="text-[11px] text-slate-400 leading-snug mb-4">{m.desc}</p>
                        </div>
                        <Link
                          href={m.href}
                          className="w-full py-1.5 rounded-lg bg-white/[0.05] hover:bg-indigo-600 hover:text-white border border-white/[0.08] text-[11px] font-semibold text-slate-300 text-center transition-colors"
                        >
                          Use Module
                        </Link>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Right 4 Columns: AI Assistant, System Status, Recent Automations */}
            <div className="lg:col-span-4 space-y-6">
              {/* Widget 1: AI Assistant Card */}
              <div className="rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06]">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-white">AI Assistant</h3>
                    <div className="flex items-center gap-1.5 text-[10px] font-mono text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      Online
                    </div>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-black/40 border border-white/[0.05] mb-4">
                  <p className="text-xs text-slate-300 leading-relaxed">
                    Hi {firstName}! 👋 <br />
                    How can I help you practice today?
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  {[
                    { label: 'Generate Content', href: '/interview/new' },
                    { label: 'Analyze Data', href: '/ats' },
                    { label: 'Create Automation', href: '/coding' },
                    { label: 'Find Insights', href: '/analytics' },
                  ].map((p) => (
                    <Link
                      key={p.label}
                      href={p.href}
                      className="p-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.08] border border-white/[0.06] text-[11px] font-medium text-slate-300 text-center transition-colors"
                    >
                      {p.label}
                    </Link>
                  ))}
                </div>
              </div>

              {/* Widget 2: System Status Card */}
              <div className="rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06]">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h3 className="text-xs font-bold text-white">System Status</h3>
                    <span className="text-[10px] font-mono text-emerald-400">All systems operational</span>
                  </div>
                  <ShieldCheck className="w-4 h-4 text-emerald-400" />
                </div>

                <div className="space-y-2.5 text-xs font-mono">
                  {[
                    'AI Engine',
                    'Data Processing',
                    'Integrations',
                    'Automation Engine',
                    'API Services',
                  ].map((srv) => (
                    <div key={srv} className="flex items-center justify-between text-slate-300">
                      <span className="text-[11px]">{srv}</span>
                      <span className="text-[10px] text-emerald-400 font-semibold flex items-center gap-1">
                        Operational <Check className="w-3 h-3" />
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Widget 3: Recent Automations List */}
              <div className="rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06]">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xs font-bold text-white">Recent Automations</h3>
                  <Link href="/analytics" className="text-[10px] font-mono text-indigo-400 hover:underline">
                    View All &gt;
                  </Link>
                </div>

                <div className="space-y-3">
                  {[
                    { name: 'Lead Nurture Flow', icon: Zap, status: 'Active' },
                    { name: 'Welcome Email Series', icon: FileText, status: 'Active' },
                    { name: 'Consent Generation', icon: Code2, status: 'Active' },
                    { name: 'Re-engagement Flow', icon: Flame, status: 'Active' },
                    { name: 'CRM Data Sync', icon: DatabaseIcon, status: 'Active' },
                  ].map((item, idx) => {
                    const Icon = item.icon
                    return (
                      <div key={idx} className="flex items-center justify-between p-2 rounded-xl bg-white/[0.02]">
                        <div className="flex items-center gap-2.5">
                          <div className="w-6 h-6 rounded-lg bg-indigo-500/15 flex items-center justify-center text-indigo-400">
                            <Icon className="w-3 h-3" />
                          </div>
                          <span className="text-xs font-medium text-slate-200">{item.name}</span>
                        </div>
                        <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                          {item.status}
                        </span>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          {/* ── BOTTOM SECTION: CHOOSE YOUR PLAN & PROMOTIONAL CARD ────────── */}
          <section id="pricing" className="pt-4 border-t border-white/[0.06]">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
              {/* Choose Your Plan Controls (2 cols) */}
              <div className="lg:col-span-2 rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-center space-y-4">
                <h3 className="text-sm font-bold text-white">Choose Your Plan</h3>
                <div className="p-1 rounded-xl bg-black/40 border border-white/[0.08] flex items-center">
                  <button
                    onClick={() => setBillingCycle('monthly')}
                    className={`flex-1 py-1.5 text-[11px] font-semibold rounded-lg transition-all ${
                      billingCycle === 'monthly' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400'
                    }`}
                  >
                    Monthly
                  </button>
                  <button
                    onClick={() => setBillingCycle('yearly')}
                    className={`flex-1 py-1.5 text-[11px] font-semibold rounded-lg transition-all ${
                      billingCycle === 'yearly' ? 'bg-indigo-600 text-white shadow' : 'text-slate-400'
                    }`}
                  >
                    Yearly
                  </button>
                </div>
                <p className="text-[11px] text-indigo-300 font-mono">Save up to 30% with yearly billing.</p>
              </div>

              {/* Starter Plan (2.5 cols) */}
              <div className="lg:col-span-2 rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                <div>
                  <div className="text-xs font-semibold text-slate-400 mb-1">Starter</div>
                  <div className="text-2xl font-black text-white font-mono mb-1">
                    $29 <span className="text-[10px] text-slate-400 font-normal">/month</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mb-4 font-mono">Billed yearly</div>
                  <ul className="space-y-2 text-[11px] text-slate-300">
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> 1,000 AI Credits
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> 10 Automations
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Basic Integrations
                    </li>
                  </ul>
                </div>
                <button className="w-full mt-6 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-white border border-white/10 transition-colors">
                  Get Started
                </button>
              </div>

              {/* Pro Plan (Most Popular) (2.5 cols) */}
              <div className="lg:col-span-3 rounded-2xl p-5 bg-gradient-to-b from-[#151838] to-[#0e1129] border-2 border-indigo-500 shadow-[0_0_30px_rgba(99,102,241,0.25)] flex flex-col justify-between relative">
                <span className="absolute -top-3 right-4 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-600 text-white shadow">
                  Most Popular
                </span>
                <div>
                  <div className="text-xs font-semibold text-indigo-300 mb-1">Pro</div>
                  <div className="text-2xl font-black text-white font-mono mb-1">
                    $79 <span className="text-[10px] text-slate-400 font-normal">/month</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mb-4 font-mono">Billed yearly</div>
                  <ul className="space-y-2 text-[11px] text-slate-200">
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> 10,000 AI Credits
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Unlimited Automations
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Advanced Integrations
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Priority Support
                    </li>
                  </ul>
                </div>
                <button className="w-full mt-6 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:brightness-110 text-xs font-bold text-white shadow-md transition-all">
                  Get Started
                </button>
              </div>

              {/* Business Plan (2.5 cols) */}
              <div className="lg:col-span-2 rounded-2xl p-5 bg-[#0d1024] border border-white/[0.06] flex flex-col justify-between">
                <div>
                  <div className="text-xs font-semibold text-slate-400 mb-1">Business</div>
                  <div className="text-2xl font-black text-white font-mono mb-1">
                    $199 <span className="text-[10px] text-slate-400 font-normal">/month</span>
                  </div>
                  <div className="text-[10px] text-slate-400 mb-4 font-mono">Billed yearly</div>
                  <ul className="space-y-2 text-[11px] text-slate-300">
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> 50,000 AI Credits
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Unlimited Everything
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Custom Integrations
                    </li>
                    <li className="flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-indigo-400" /> Dedicated Support
                    </li>
                  </ul>
                </div>
                <button className="w-full mt-6 py-2 rounded-xl bg-white/[0.05] hover:bg-white/[0.1] text-xs font-semibold text-white border border-white/10 transition-colors">
                  Get Started
                </button>
              </div>

              {/* Scale Your Career / Business Promotional Box (2.5 cols) */}
              <div className="lg:col-span-3 rounded-2xl p-5 bg-gradient-to-br from-[#121633] to-[#181a38] border border-indigo-500/25 flex flex-col justify-between">
                <div>
                  <h3 className="text-sm font-bold text-white mb-2">Scale Your Business with AI Automation</h3>
                  <p className="text-[11px] text-slate-400 leading-relaxed mb-4">
                    Join thousands of engineers already using AI to automate and grow faster.
                  </p>
                </div>

                <div className="flex items-center justify-center py-4">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-[0_0_30px_rgba(6,182,212,0.4)]">
                    <Cpu className="w-8 h-8 text-white animate-pulse" />
                  </div>
                </div>

                <button className="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-xs font-bold text-white shadow-md hover:brightness-110 transition-all">
                  Upgrade Your Plan
                </button>
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  )
}

function DatabaseIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <ellipse cx="12" cy="5" rx="9" ry="3" />
      <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      <path d="M3 12c0 1.66 4 3 9 3s9-1.34 9-3" />
    </svg>
  )
}
