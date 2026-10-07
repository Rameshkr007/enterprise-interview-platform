'use client'

import React, { useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'

interface Message {
  role: 'candidate' | 'hr'
  content: string
  tactic?: string
  score?: number
  offer?: number
  power?: string
  tip?: string
}

interface AnalysisResult {
  final_offer_achieved: number
  vs_target: number
  overall_score: number
  tactics_used: string[]
  best_moment: string
  worst_moment: string
  what_you_did_well: string[]
  mistakes_made: string[]
  pro_tips: string[]
  would_have_gotten_offer: boolean
  estimated_money_left_on_table: number
}

export default function NegotiationPage() {
  const [role, setRole] = useState('Senior Full Stack Engineer')
  const [company, setCompany] = useState('Tier-1 Tech Corp')
  const [minSalary, setMinSalary] = useState(130)
  const [maxSalary, setMaxSalary] = useState(190)
  const [currentOffer, setCurrentOffer] = useState(140)
  const [targetSalary, setTargetSalary] = useState(175)
  const [roundNum, setRoundNum] = useState(1)

  const [conversation, setConversation] = useState<Message[]>([
    {
      role: 'hr',
      content:
        "Congratulations on passing our technical interviews! We are thrilled to offer you the Senior Full Stack Engineer role with a starting base salary of $140,000. How does that sound to you?",
      offer: 140,
      power: 'balanced',
      tip: "Avoid saying 'yes' immediately. Acknowledge excitement first, then anchor higher or ask about flexibility in base and equity.",
    },
  ])

  const [inputMessage, setInputMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null)
  const [analyzing, setAnalyzing] = useState(false)

  const handleSend = async () => {
    if (!inputMessage.trim() || loading) return

    const candidateMsg = inputMessage.trim()
    setInputMessage('')
    setLoading(true)

    const updatedHistory: Message[] = [
      ...conversation,
      { role: 'candidate', content: candidateMsg },
    ]
    setConversation(updatedHistory)

    try {
      const payload = {
        role,
        company,
        min_salary: minSalary,
        max_salary: maxSalary,
        current_salary: currentOffer,
        years_exp: 5,
        candidate_message: candidateMsg,
        conversation_history: updatedHistory.map((m) => ({
          role: m.role,
          content: m.content,
        })),
        round_num: roundNum + 1,
      }

      const res = await api.post('/negotiation/round', payload)
      const data = res.data

      const newOffer = data.current_offer || currentOffer
      setCurrentOffer(newOffer)
      setRoundNum((prev) => prev + 1)

      setConversation([
        ...updatedHistory,
        {
          role: 'hr',
          content: data.hr_response,
          tactic: data.tactic_used_by_candidate,
          score: data.tactic_score,
          offer: newOffer,
          power: data.power_dynamics,
          tip: data.negotiation_tip,
        },
      ])
    } catch (err) {
      console.error('Negotiation error', err)
    } finally {
      setLoading(false)
    }
  }

  const handleFinishAndAnalyze = async () => {
    setAnalyzing(true)
    try {
      const res = await api.post('/negotiation/analyze', {
        target_salary: targetSalary,
        conversation_history: conversation.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      })
      setAnalysis(res.data)
    } catch (err) {
      console.error('Analysis error', err)
    } finally {
      setAnalyzing(false)
    }
  }

  const lastHrMessage = [...conversation].reverse().find((m) => m.role === 'hr')

  return (
    <div className="min-h-screen max-w-6xl mx-auto px-4 py-8 animate-fade-in text-slate-100 flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-white/10 gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-2xl">💰</span>
            <h1 className="text-2xl font-black tracking-tight text-white">
              Salary Negotiation Arena
            </h1>
            <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 font-bold border border-emerald-500/30 uppercase">
              Live Simulator
            </span>
          </div>
          <p className="text-sm text-slate-400">
            Spar with an aggressive AI HR recruiter. Learn leverage, anchoring, and win thousands in real life.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="btn-ghost text-sm py-2 px-4">
            ← Dashboard
          </Link>
          <button
            onClick={handleFinishAndAnalyze}
            disabled={conversation.length < 3 || analyzing}
            className="btn-primary text-sm py-2 px-4 shadow-lg shadow-brand-500/20"
          >
            {analyzing ? 'Analyzing Game...' : '📊 Conclude & Score Strategy'}
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Negotiation Parameters & HUD */}
        <div className="lg:col-span-4 flex flex-col gap-5">
          {/* Compensation Gauge Card */}
          <div className="glass-card p-5 border border-white/10 rounded-2xl bg-slate-900/60 shadow-xl space-y-4">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Offer Tracker
            </h3>
            <div className="flex items-baseline justify-between">
              <div>
                <span className="text-3xl font-extrabold text-emerald-400">
                  ${currentOffer}k
                </span>
                <span className="text-xs text-slate-400 ml-1">current offer</span>
              </div>
              <div className="text-right">
                <span className="text-sm font-semibold text-brand-300">
                  ${targetSalary}k
                </span>
                <span className="text-xs text-slate-400 block">target goal</span>
              </div>
            </div>

            {/* Visual range bar */}
            <div className="relative pt-2">
              <div className="h-2.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
                <div
                  className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 rounded-full transition-all duration-700"
                  style={{
                    width: `${Math.min(
                      100,
                      Math.max(
                        5,
                        ((currentOffer - minSalary) / (maxSalary - minSalary)) * 100
                      )
                    )}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-slate-500 mt-1.5 font-mono">
                <span>${minSalary}k</span>
                <span>Band: ${minSalary}k - ${maxSalary}k</span>
                <span>${maxSalary}k</span>
              </div>
            </div>

            {/* Dynamics indicator */}
            <div className="p-3 rounded-xl bg-white/5 border border-white/5 flex items-center justify-between">
              <span className="text-xs text-slate-400">Power Dynamics:</span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded capitalize ${
                  lastHrMessage?.power === 'candidate_winning'
                    ? 'text-emerald-400 bg-emerald-500/10'
                    : lastHrMessage?.power === 'hr_winning'
                    ? 'text-rose-400 bg-rose-500/10'
                    : 'text-amber-400 bg-amber-500/10'
                }`}
              >
                {lastHrMessage?.power?.replace('_', ' ') || 'Balanced'}
              </span>
            </div>
          </div>

          {/* Configuration Settings */}
          <div className="glass-card p-5 border border-white/10 rounded-2xl bg-slate-900/60 shadow-xl space-y-3.5">
            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
              Scenario Setup
            </h3>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Target Position</label>
              <input
                type="text"
                className="input-field text-xs py-2"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs text-slate-400 block mb-1">Company Persona</label>
              <input
                type="text"
                className="input-field text-xs py-2"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Min Band ($k)</label>
                <input
                  type="number"
                  className="input-field text-xs py-2"
                  value={minSalary}
                  onChange={(e) => setMinSalary(Number(e.target.value))}
                />
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Max Band ($k)</label>
                <input
                  type="number"
                  className="input-field text-xs py-2"
                  value={maxSalary}
                  onChange={(e) => setMaxSalary(Number(e.target.value))}
                />
              </div>
            </div>
          </div>

          {/* Real-time Tactic Coach Callout */}
          {lastHrMessage?.tip && (
            <div className="glass-card p-4 border border-amber-400/20 bg-amber-500/5 rounded-2xl">
              <div className="flex items-center gap-2 text-xs font-bold text-amber-300 mb-1">
                <span>💡</span>
                <span>Pro Counter-Move Suggestion</span>
              </div>
              <p className="text-xs text-amber-100/80 leading-relaxed">
                {lastHrMessage.tip}
              </p>
            </div>
          )}
        </div>

        {/* Right Column: Interactive Chat Dialogue Stream */}
        <div className="lg:col-span-8 flex flex-col h-[650px] glass-card border border-white/10 rounded-2xl bg-slate-900/60 shadow-2xl overflow-hidden">
          {/* Chat Messages Log */}
          <div className="flex-1 p-5 overflow-y-auto space-y-4">
            {conversation.map((msg, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  msg.role === 'candidate' ? 'items-end' : 'items-start'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-bold text-slate-400">
                    {msg.role === 'candidate' ? 'You (Candidate)' : `HR Recruiter (${company})`}
                  </span>
                  {msg.tactic && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-brand-500/20 text-brand-300 border border-brand-500/30">
                      Tactic: {msg.tactic}
                    </span>
                  )}
                  {msg.score !== undefined && (
                    <span className="text-[10px] text-emerald-400 font-semibold">
                      +{Math.round(msg.score * 100)} pts
                    </span>
                  )}
                </div>
                <div
                  className={`p-4 rounded-2xl max-w-[85%] text-sm leading-relaxed ${
                    msg.role === 'candidate'
                      ? 'bg-brand-600 text-white rounded-tr-none'
                      : 'bg-white/10 text-slate-200 border border-white/10 rounded-tl-none'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-slate-400 p-2">
                <span className="w-2 h-2 rounded-full bg-brand-400 animate-ping" />
                HR is preparing counter-argument...
              </div>
            )}
          </div>

          {/* Interactive Input Bar */}
          <div className="p-4 border-t border-white/10 bg-slate-950/70 flex items-center gap-3">
            <input
              type="text"
              className="input-field flex-1 py-3 text-sm bg-slate-900/80"
              placeholder="E.g., Thank you for the offer. Based on my distributed systems leadership and market research, I am targeting $175,000..."
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              disabled={loading}
            />
            <button
              onClick={handleSend}
              disabled={!inputMessage.trim() || loading}
              className="btn-primary py-3 px-6 text-sm flex-shrink-0"
            >
              Negotiate →
            </button>
          </div>
        </div>
      </div>

      {/* Analysis Modal */}
      {analysis && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="glass-card max-w-2xl w-full p-6 md:p-8 rounded-3xl border border-white/20 bg-slate-900 shadow-2xl max-h-[90vh] overflow-y-auto space-y-6">
            <div className="flex items-center justify-between border-b border-white/10 pb-4">
              <div>
                <h2 className="text-xl font-black text-white">Negotiation Scorecard</h2>
                <p className="text-xs text-slate-400">AI Financial & Strategic Performance Audit</p>
              </div>
              <button
                onClick={() => setAnalysis(null)}
                className="text-slate-400 hover:text-white text-lg p-2"
              >
                ✕
              </button>
            </div>

            {/* Scorecard Hero */}
            <div className="grid grid-cols-3 gap-4 text-center">
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                <div className="text-3xl font-extrabold text-emerald-400">
                  ${analysis.final_offer_achieved}k
                </div>
                <div className="text-xs text-slate-400 mt-1">Final Base Achieved</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                <div className="text-3xl font-extrabold text-brand-400">
                  {Math.round(analysis.overall_score * 100)}%
                </div>
                <div className="text-xs text-slate-400 mt-1">Tactical Score</div>
              </div>
              <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                <div className="text-3xl font-extrabold text-amber-400">
                  ${analysis.estimated_money_left_on_table}k
                </div>
                <div className="text-xs text-slate-400 mt-1">Left on Table</div>
              </div>
            </div>

            {/* Key Findings */}
            <div className="space-y-4">
              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                <h4 className="text-xs font-bold text-emerald-300 uppercase mb-1">What You Did Well</h4>
                <ul className="text-xs text-emerald-100/90 list-disc list-inside space-y-1">
                  {analysis.what_you_did_well.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20">
                <h4 className="text-xs font-bold text-rose-300 uppercase mb-1">Areas for Improvement</h4>
                <ul className="text-xs text-rose-100/90 list-disc list-inside space-y-1">
                  {analysis.mistakes_made.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="p-4 rounded-xl bg-brand-500/10 border border-brand-500/20">
                <h4 className="text-xs font-bold text-brand-300 uppercase mb-1">Pro Tips for Real Life</h4>
                <ul className="text-xs text-brand-100/90 list-disc list-inside space-y-1">
                  {analysis.pro_tips.map((item, i) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>

            <button
              onClick={() => setAnalysis(null)}
              className="btn-primary w-full py-3 text-sm"
            >
              Continue Practicing
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
