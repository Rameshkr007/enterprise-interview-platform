'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  Bell,
  Moon,
  Sun,
  LogOut,
  Sparkles,
  Command,
  CheckCircle2,
  ShieldCheck,
} from 'lucide-react'

interface TopbarProps {
  userName: string
  userEmail: string
  tier: string
  credits: number
  onOpenCommandPalette: () => void
  onOpenUpgrade: () => void
  onLogout: () => void
}

export default function Topbar({
  userName,
  userEmail,
  tier,
  credits,
  onOpenCommandPalette,
  onOpenUpgrade,
  onLogout,
}: TopbarProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isDarkMode, setIsDarkMode] = useState(true)

  const firstName = userName?.split(' ')[0] || 'Engineer'

  return (
    <header className="h-18 px-6 py-4 border-b border-white/[0.06] bg-[#070814]/85 backdrop-blur-xl flex items-center justify-between gap-4 sticky top-0 z-20">
      {/* Search Input triggering Command Palette */}
      <div className="relative flex-1 max-w-md">
        <button
          type="button"
          onClick={onOpenCommandPalette}
          className="w-full flex items-center justify-between px-3.5 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-xs text-slate-400 text-left transition-all group"
        >
          <div className="flex items-center gap-2.5">
            <Search className="w-4 h-4 text-slate-400 group-hover:text-cyan-400 transition-colors" />
            <span>Search interviews, modules, skills...</span>
          </div>
          <kbd className="text-[10px] font-mono text-slate-400 bg-white/[0.08] px-2 py-0.5 rounded border border-white/10 flex items-center gap-1">
            <Command className="w-3 h-3" /> K
          </kbd>
        </button>
      </div>

      {/* Live System Status Badges */}
      <div className="hidden xl:flex items-center gap-4 text-[11px] font-mono text-slate-400">
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          RENDER: HEALTHY
        </span>
        <span className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          PGVECTOR: 1536D
        </span>
      </div>

      {/* Right Action Icons & User Profile */}
      <div className="flex items-center gap-3 relative">
        {/* Plan & Credits Pill */}
        <button
          onClick={onOpenUpgrade}
          className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-mono hover:bg-indigo-500/20 transition-all cursor-pointer"
        >
          <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
          <span className="font-semibold">{tier}</span>
          <span className="text-[10px] text-slate-400 font-normal">({credits.toLocaleString()} AI Credits)</span>
        </button>

        {/* Notifications Bell */}
        <div className="relative">
          <button
            onClick={() => setShowNotifications(!showNotifications)}
            aria-label="View notifications"
            className="relative p-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-slate-300 hover:text-white transition-colors"
          >
            <Bell className="w-4 h-4" />
            <span className="w-2 h-2 rounded-full bg-cyan-400 absolute top-1.5 right-1.5 animate-pulse" />
          </button>

          {showNotifications && (
            <div className="absolute right-0 mt-2 w-80 rounded-2xl bg-[#0f1228] border border-indigo-500/30 shadow-2xl p-4 space-y-3 z-50 animate-slide-up">
              <div className="flex items-center justify-between pb-2 border-b border-white/[0.06]">
                <span className="text-xs font-bold text-white">System Telemetry &amp; Alerts</span>
                <span className="text-[10px] font-mono text-emerald-400">All Systems Operational</span>
              </div>
              <div className="space-y-2 text-xs">
                <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                  <div className="font-semibold text-white">FastAPI Core Active</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Render backend responding in sub-120ms latency.</div>
                </div>
                <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                  <div className="font-semibold text-white">Daily Streak Reward</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Day 4 streak multiplier active for today&apos;s challenge.</div>
                </div>
                <div className="p-2.5 rounded-xl bg-white/[0.03] border border-white/[0.05]">
                  <div className="font-semibold text-white">1536d Embeddings Synced</div>
                  <div className="text-[10px] text-slate-400 mt-0.5">Supabase PGVector ready for instant resume alignment.</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Dark/Ambient Toggle */}
        <button
          onClick={() => setIsDarkMode(!isDarkMode)}
          title="Toggle display mode"
          className="p-2 rounded-xl bg-white/[0.03] border border-white/[0.08] text-slate-300 hover:text-white transition-colors"
        >
          {isDarkMode ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4 text-amber-400" />}
        </button>

        {/* User Profile Chip */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-2.5 pl-2 border-l border-white/[0.08] text-left hover:opacity-90 transition-opacity"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 via-indigo-600 to-purple-600 flex items-center justify-center font-bold text-sm text-white shadow-md">
              {firstName.charAt(0)}
            </div>
            <div className="text-left hidden sm:block">
              <div className="text-xs font-bold text-white leading-tight">{userName}</div>
              <div className="text-[10px] font-mono text-cyan-400 leading-tight">{tier}</div>
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-[#0f1228] border border-white/10 shadow-2xl p-3 space-y-2 z-50 animate-slide-up">
              <div className="px-3 py-2 border-b border-white/[0.06]">
                <div className="text-xs font-bold text-white">{userName}</div>
                <div className="text-[10px] text-slate-400 truncate">{userEmail}</div>
                <div className="text-[10px] font-mono text-emerald-400 mt-1">
                  Credits: {credits.toLocaleString()} AI Credits
                </div>
              </div>
              <button
                onClick={() => {
                  setShowUserMenu(false)
                  onOpenUpgrade()
                }}
                className="w-full px-3 py-2 rounded-lg text-left text-xs font-semibold text-indigo-300 hover:bg-white/[0.05] transition-colors flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Subscription &amp; Plans</span>
              </button>
              <button
                onClick={onLogout}
                className="w-full px-3 py-2 rounded-lg text-left text-xs font-semibold text-red-400 hover:bg-white/[0.05] transition-colors flex items-center gap-2 cursor-pointer"
              >
                <LogOut className="w-3.5 h-3.5" />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
