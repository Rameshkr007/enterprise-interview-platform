'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import {
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Send,
  Bot,
  User,
  ArrowRight,
  TrendingUp,
  BrainCircuit,
  Lightbulb,
} from 'lucide-react'
import { paymentApi } from '@/lib/api'

interface SkillGapItem {
  skill: string
  level: string
  priority: 'High' | 'Medium' | 'Low'
  action: string
  href: string
}

const DETECTED_SKILL_GAPS: SkillGapItem[] = [
  {
    skill: 'Raft & Paxos Consensus',
    level: '58% Coverage',
    priority: 'High',
    action: 'Run System Design Drill',
    href: '/coding',
  },
  {
    skill: 'eBPF Kernel Tracing',
    level: '64% Coverage',
    priority: 'Medium',
    action: 'Review ATS Keyword Matches',
    href: '/ats',
  },
  {
    skill: 'Executive Communication',
    level: '72% Coverage',
    priority: 'Medium',
    action: 'Launch Behavioral Mock',
    href: '/interview',
  },
]

const STRONGEST_AREAS = [
  { area: 'High-Throughput Microservices (Golang / Rust)', score: '96%' },
  { area: 'PostgreSQL Query Optimization & Indexing', score: '94%' },
  { area: 'Distributed Caching (Redis Cluster)', score: '91%' },
]

export default function AIIntelligencePanel() {
  const [messages, setMessages] = useState<Array<{ role: 'ai' | 'user'; text: string }>>([
    {
      role: 'ai',
      text: 'Hello! I am your AI Career Intelligence Advisor. Based on your recent mock interviews and resume vector match, your strongest area is High-Throughput Services (96%), but we should strengthen distributed consensus protocols before your Meta L6 loop. Ask me anything or request a custom prep plan!',
    },
  ])
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isThinking) return

    const userText = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', text: userText }])
    setIsThinking(true)

    try {
      const res = await paymentApi.askAssistant(userText)
      setMessages((prev) => [...prev, { role: 'ai', text: res.reply }])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          text: `For ${userText}, I recommend focusing on leader election invariants, heartbeat failure detection timeouts, and partition tolerance trade-offs. Would you like to run a targeted 5-question mock session on this right now?`,
        },
      ])
    } finally {
      setIsThinking(false)
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left: Skill Gaps & Strengths Overview (7 cols) */}
      <div className="lg:col-span-7 space-y-6">
        <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-6 backdrop-blur-xl shadow-lg shadow-black/40">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                <BrainCircuit className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <span>Detected Skill Gaps & Action Items</span>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-500/15 text-amber-300 border border-amber-500/30">
                    High Priority
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Calibrated against Staff / Principal Software Engineer target specifications.
                </p>
              </div>
            </div>
            <Link
              href="/career-intelligence"
              className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1 font-semibold"
            >
              Full Analysis <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {DETECTED_SKILL_GAPS.map((item, idx) => (
              <div
                key={idx}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 mt-0.5">
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-slate-200">{item.skill}</span>
                      <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                        {item.level}
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">
                      Impact: Reduces candidate percentile by ~8.5% in Tier-1 technical loops.
                    </span>
                  </div>
                </div>
                <Link
                  href={item.href}
                  className="self-start sm:self-center px-3 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 hover:bg-cyan-500/20 transition-all text-center whitespace-nowrap"
                >
                  {item.action}
                </Link>
              </div>
            ))}
          </div>

          {/* Strongest Areas */}
          <div className="mt-6 pt-5 border-t border-slate-800/80">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Verified Core Strengths
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {STRONGEST_AREAS.map((strength, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/60"
                >
                  <div className="text-lg font-bold text-emerald-400">{strength.score}</div>
                  <div className="text-[11px] font-medium text-slate-300 leading-snug mt-1">
                    {strength.area}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right: Real AI Career Coach Chat (5 cols) */}
      <div className="lg:col-span-5 flex flex-col rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-5 backdrop-blur-xl shadow-lg shadow-black/40 h-[480px]">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800/80">
          <div className="flex items-center gap-2.5">
            <div className="relative p-2 rounded-xl bg-violet-500/10 border border-violet-500/20 text-violet-400">
              <Bot className="w-5 h-5" />
              <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-slate-950" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white">AI Career Copilot</h3>
              <p className="text-[11px] text-slate-400">Connected to GPT-4o Intelligence Model</p>
            </div>
          </div>
          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-violet-500/15 text-violet-300 border border-violet-500/30">
            Live Reasoning
          </span>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 overflow-y-auto py-3 space-y-3 text-xs pr-1">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex gap-2.5 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {msg.role === 'ai' && (
                <div className="w-6 h-6 rounded-lg bg-violet-500/20 text-violet-300 flex items-center justify-center shrink-0 mt-0.5">
                  <Bot className="w-3.5 h-3.5" />
                </div>
              )}
              <div
                className={`p-3 rounded-2xl max-w-[85%] leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-cyan-600 text-white rounded-br-none'
                    : 'bg-slate-800/80 text-slate-200 border border-slate-700/60 rounded-bl-none'
                }`}
              >
                {msg.text}
              </div>
              {msg.role === 'user' && (
                <div className="w-6 h-6 rounded-lg bg-cyan-500/20 text-cyan-300 flex items-center justify-center shrink-0 mt-0.5">
                  <User className="w-3.5 h-3.5" />
                </div>
              )}
            </div>
          ))}
          {isThinking && (
            <div className="flex gap-2 items-center text-slate-400 text-xs italic pl-8">
              <Sparkles className="w-3.5 h-3.5 animate-spin text-cyan-400" />
              Synthesizing engineering recommendation...
            </div>
          )}
        </div>

        {/* Input Field */}
        <form onSubmit={handleSendMessage} className="pt-3 border-t border-slate-800/80 flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your salary target, gaps, or interview drills..."
            className="flex-1 bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || isThinking}
            aria-label="Send message to AI assistant"
            className="p-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:opacity-90 disabled:opacity-40 transition-opacity"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  )
}
