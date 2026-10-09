'use client'

import React, { useState, useEffect, useRef } from 'react'
import { useRouter } from 'next/navigation'
import {
  Search,
  X,
  Mic,
  FileText,
  Code2,
  Cpu,
  Building2,
  Coins,
  Sparkles,
  Briefcase,
  Flame,
  BarChart3,
  Settings,
  ArrowRight,
} from 'lucide-react'

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
}

export default function CommandPalette({ isOpen, onClose }: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const router = useRouter()
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50)
    } else {
      setQuery('')
    }
  }, [isOpen])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  const commands = [
    { name: 'AI Mock Interview', desc: 'Launch adaptive multi-turn interview with biometric scoring', icon: Mic, href: '/interview/new', tag: 'Simulation' },
    { name: 'ATS Resume Analyzer', desc: '1536d PGVector cosine semantic skill matching', icon: FileText, href: '/ats', tag: 'Intelligence' },
    { name: 'AI Coding Studio', desc: 'In-browser algorithmic challenge execution', icon: Code2, href: '/coding', tag: 'Technical' },
    { name: 'System Design Board', desc: 'Distributed architecture and tradeoff calibration', icon: Cpu, href: '/system-design', tag: 'Technical' },
    { name: 'Company Mode', desc: 'Google, Amazon LP, Meta, and Microsoft rubrics', icon: Building2, href: '/company-mode', tag: 'Simulation' },
    { name: 'Salary Negotiation', desc: 'Interactive corporate recruiter compensation sparring', icon: Coins, href: '/negotiation', tag: 'Career' },
    { name: 'Career Intelligence', desc: 'STAR-formatted resume rewriting and roadmap', icon: Sparkles, href: '/resume-builder', tag: 'Intelligence' },
    { name: 'Job Application Tracker', desc: 'Full-lifecycle Kanban application CRM', icon: Briefcase, href: '/job-tracker', tag: 'Pipeline' },
    { name: 'Daily Technical Challenge', desc: 'Spaced repetition technical interview retention', icon: Flame, href: '/daily-challenge', tag: 'Daily' },
    { name: 'Analytics & Ranking', desc: 'Acoustic pitch stability, pause ratios, and leaderboard', icon: BarChart3, href: '/analytics', tag: 'Telemetry' },
    { name: 'Platform Diagnostics', desc: 'Inspect database, cache, and model latency', icon: Settings, href: '/admin/diagnostics', tag: 'Platform' },
  ]

  const filtered = commands.filter(
    (c) =>
      c.name.toLowerCase().includes(query.toLowerCase()) ||
      c.desc.toLowerCase().includes(query.toLowerCase()) ||
      c.tag.toLowerCase().includes(query.toLowerCase())
  )

  const handleSelect = (href: string) => {
    onClose()
    router.push(href)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4 bg-black/80 backdrop-blur-md animate-fade-in">
      <div className="relative w-full max-w-xl rounded-2xl bg-[#0d1024] border border-indigo-500/30 shadow-[0_20px_70px_rgba(0,0,0,0.8)] overflow-hidden">
        {/* Search Input Bar */}
        <div className="p-4 border-b border-white/[0.08] flex items-center gap-3 bg-[#0a0c1c]">
          <Search className="w-5 h-5 text-cyan-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Type a command, module, or skill to navigate..."
            className="w-full bg-transparent text-sm text-white placeholder-slate-400 focus:outline-none"
          />
          <kbd className="text-[10px] font-mono text-slate-400 bg-white/[0.08] px-2 py-0.5 rounded border border-white/10 shrink-0">
            ESC
          </kbd>
          <button
            onClick={onClose}
            aria-label="Close command palette"
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Results List */}
        <div className="max-h-80 overflow-y-auto p-2 space-y-1">
          {filtered.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-400 font-mono">
              No matching modules or actions found.
            </div>
          ) : (
            filtered.map((item) => {
              const Icon = item.icon
              return (
                <button
                  key={item.name}
                  onClick={() => handleSelect(item.href)}
                  className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-white/[0.05] hover:border-indigo-500/30 border border-transparent transition-all text-left group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-indigo-500/15 border border-indigo-500/30 flex items-center justify-center text-indigo-400 group-hover:text-cyan-400 transition-colors shrink-0">
                      <Icon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="text-xs font-bold text-white group-hover:text-cyan-300 transition-colors">
                        {item.name}
                      </div>
                      <div className="text-[11px] text-slate-400 line-clamp-1">{item.desc}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-white/[0.05] border border-white/10 text-slate-400">
                      {item.tag}
                    </span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:text-cyan-400 group-hover:translate-x-1 transition-all" />
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>
    </div>
  )
}
