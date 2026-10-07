'use client'
import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'

const COMPANIES = [
  { key: 'google',    name: 'Google',     emoji: '🔍', color: '#4285f4', difficulty: 'Hard' },
  { key: 'amazon',    name: 'Amazon',     emoji: '📦', color: '#ff9900', difficulty: 'Hard' },
  { key: 'microsoft', name: 'Microsoft',  emoji: '🪟', color: '#00a4ef', difficulty: 'Medium' },
  { key: 'meta',      name: 'Meta',       emoji: '🌐', color: '#1877f2', difficulty: 'Hard' },
  { key: 'startup',   name: 'Startup',    emoji: '🚀', color: '#10b981', difficulty: 'Medium' },
]

interface Question {
  question_text: string
  category: string
  company_principle: string
  what_they_look_for: string
  rationale: string
  red_flags_to_avoid: string[]
  model_answer_structure: string
  company_name: string
  red_flags: string[]
}

interface CultureFitResult {
  culture_fit_score: number
  principle_alignment: Array<{ principle: string; score: number; evidence: string }>
  framework_used: boolean
  specific_examples_given: boolean
  impact_quantified: boolean
  feedback: string
  what_would_impress_them_more: string
  behavioral_framework: string
}

export default function CompanyModePage() {
  const [selectedCompany, setSelectedCompany] = useState<string | null>(null)
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [focus, setFocus] = useState('behavioral')
  const [question, setQuestion] = useState<Question | null>(null)
  const [answer, setAnswer] = useState('')
  const [fitResult, setFitResult] = useState<CultureFitResult | null>(null)
  const [phase, setPhase] = useState<'select' | 'question' | 'answer' | 'result'>('select')

  const questionMutation = useMutation({
    mutationFn: () => api.post('/game/company/question', {
      company: selectedCompany,
      difficulty,
      focus_area: focus,
      skill_gaps: [],
    }).then(r => r.data),
    onSuccess: (data) => { setQuestion(data); setPhase('answer') },
  })

  const fitMutation = useMutation({
    mutationFn: () => api.post('/game/company/culture-fit', {
      company: selectedCompany,
      question: question?.question_text,
      answer,
    }).then(r => r.data),
    onSuccess: (data) => { setFitResult(data); setPhase('result') },
  })

  const comp = COMPANIES.find(c => c.key === selectedCompany)

  if (phase === 'select') {
    return (
      <div className="min-h-screen max-w-4xl mx-auto px-6 py-12 animate-fade-in">
        <div className="flex items-center justify-between mb-10">
          <div>
            <h1 className="text-3xl font-bold text-white mb-1">🏢 Company Interview Mode</h1>
            <p className="text-slate-400">Practice with real company interview patterns and culture scoring</p>
          </div>
          <Link href="/dashboard" className="btn-ghost">← Dashboard</Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 mb-8">
          {COMPANIES.map(c => (
            <button
              key={c.key}
              onClick={() => { setSelectedCompany(c.key); setPhase('question') }}
              className={`glass-card p-7 text-left group hover:scale-[1.02] transition-all border-2 ${
                selectedCompany === c.key ? 'border-brand-500' : 'border-transparent hover:border-white/20'
              }`}
            >
              <div className="text-5xl mb-4">{c.emoji}</div>
              <div className="text-xl font-bold text-white mb-1">{c.name}</div>
              <div className="flex items-center gap-2 mb-3">
                <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                  c.difficulty === 'Hard' ? 'bg-red-500/20 text-red-400' : 'bg-amber-500/20 text-amber-400'
                }`}>{c.difficulty}</span>
              </div>
              <div
                className="w-full h-1 rounded-full opacity-60"
                style={{ background: c.color }}
              />
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (phase === 'question') {
    return (
      <div className="min-h-screen max-w-2xl mx-auto px-6 py-12 animate-fade-in">
        <div className="flex items-center gap-4 mb-10">
          <button onClick={() => setPhase('select')} className="btn-ghost text-sm">← Back</button>
          <div className="flex items-center gap-3">
            <span className="text-3xl">{comp?.emoji}</span>
            <div>
              <div className="text-white font-bold">{comp?.name} Interview</div>
              <div className="text-slate-400 text-sm">Configure your practice round</div>
            </div>
          </div>
        </div>

        <div className="glass-card p-8 space-y-6">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-3">Difficulty</label>
            <div className="flex gap-3">
              {(['easy', 'medium', 'hard'] as const).map(d => (
                <button key={d} onClick={() => setDifficulty(d)}
                        className={`flex-1 py-2.5 rounded-xl text-sm font-medium capitalize border transition-all ${
                          difficulty === d
                            ? d === 'hard' ? 'bg-red-500/20 border-red-500/50 text-red-300'
                            : d === 'medium' ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                            : 'bg-green-500/20 border-green-500/50 text-green-300'
                            : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                        }`}>
                  {d}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-3">Focus Area</label>
            <select className="input-field" value={focus} onChange={e => setFocus(e.target.value)}>
              <option value="behavioral">Behavioral / Leadership</option>
              <option value="technical">Technical</option>
              <option value="system_design">System Design</option>
              <option value="culture_fit">Culture Fit</option>
            </select>
          </div>

          {selectedCompany === 'amazon' && (
            <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-500/20">
              <div className="text-amber-400 text-xs font-bold mb-2">⚡ Amazon LP Mode</div>
              <p className="text-slate-300 text-xs">Questions will be anchored to Amazon's 14 Leadership Principles. Use STAR format in every answer.</p>
            </div>
          )}

          <button
            id="generate-company-question-btn"
            onClick={() => questionMutation.mutate()}
            disabled={questionMutation.isPending}
            className="btn-primary w-full py-4 text-base"
          >
            {questionMutation.isPending ? `🤖 Preparing ${comp?.name} Interview...` : `🚀 Start ${comp?.name} Interview`}
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'answer' && question) {
    return (
      <div className="min-h-screen max-w-3xl mx-auto px-6 py-12 animate-fade-in">
        <div className="flex items-center gap-3 mb-8">
          <span className="text-3xl">{comp?.emoji}</span>
          <div>
            <div className="text-white font-bold">{comp?.name} — {question.company_principle}</div>
            <div className="text-slate-400 text-sm capitalize">{question.category} • {difficulty}</div>
          </div>
        </div>

        {/* Question card */}
        <div className="glass-card p-8 mb-6" style={{ borderColor: `${comp?.color}30`, borderWidth: 1 }}>
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-xl flex items-center justify-center text-xl flex-shrink-0"
                 style={{ background: `${comp?.color}20` }}>
              {comp?.emoji}
            </div>
            <div>
              <div className="text-xs text-slate-500 mb-2">Interview Question</div>
              <p className="text-white text-lg font-medium leading-relaxed">{question.question_text}</p>
            </div>
          </div>
        </div>

        {/* Context */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className="glass-card p-4">
            <div className="text-xs text-slate-500 mb-2">What they look for</div>
            <p className="text-slate-300 text-sm">{question.what_they_look_for}</p>
          </div>
          <div className="glass-card p-4">
            <div className="text-xs text-slate-500 mb-2">Answer structure ({question.model_answer_structure})</div>
            <p className="text-slate-300 text-sm">{question.model_answer_structure}</p>
          </div>
        </div>

        {/* Answer input */}
        <div className="glass-card p-6">
          <label className="block text-sm font-semibold text-white mb-3">Your Answer</label>
          <textarea
            id="company-answer-input"
            className="w-full bg-white/5 text-slate-200 rounded-xl p-4 resize-none border border-white/10 focus:border-brand-500/50 focus:outline-none text-sm leading-relaxed"
            rows={8}
            placeholder={`Use the ${question.model_answer_structure} format. Be specific with examples and quantify your impact...`}
            value={answer}
            onChange={e => setAnswer(e.target.value)}
          />

          {/* Red flags warning */}
          <div className="mt-4 p-3 rounded-xl bg-red-500/8 border border-red-500/15">
            <div className="text-xs text-red-400 font-medium mb-1.5">⚠️ Avoid these red flags</div>
            <div className="flex flex-wrap gap-2">
              {question.red_flags_to_avoid.map((f, i) => (
                <span key={i} className="text-xs text-red-300/70 bg-red-500/10 px-2 py-0.5 rounded">{f}</span>
              ))}
            </div>
          </div>

          <button
            id="submit-company-answer-btn"
            onClick={() => fitMutation.mutate()}
            disabled={answer.trim().length < 50 || fitMutation.isPending}
            className="btn-primary w-full mt-5 py-4"
          >
            {fitMutation.isPending ? '🔍 Analyzing culture fit...' : '🎯 Submit & Score Culture Fit'}
          </button>
        </div>
      </div>
    )
  }

  if (phase === 'result' && fitResult && question) {
    const score = Math.round(fitResult.culture_fit_score * 100)
    const scoreColor = score >= 80 ? '#10b981' : score >= 60 ? '#f59e0b' : '#ef4444'
    return (
      <div className="min-h-screen max-w-3xl mx-auto px-6 py-12 animate-fade-in space-y-6">
        {/* Score hero */}
        <div className="glass-card p-10 text-center" style={{ borderColor: `${scoreColor}30`, borderWidth: 1 }}>
          <div className="text-7xl font-black mb-2" style={{ color: scoreColor }}>{score}</div>
          <div className="text-slate-400 mb-1">Culture Fit Score</div>
          <div className="text-2xl">{comp?.emoji} {comp?.name}</div>
          <div className="flex justify-center gap-6 mt-6 text-sm">
            {[
              { label: `${fitResult.behavioral_framework} Used`, val: fitResult.framework_used },
              { label: 'Specific Examples', val: fitResult.specific_examples_given },
              { label: 'Impact Quantified', val: fitResult.impact_quantified },
            ].map(m => (
              <div key={m.label} className="text-center">
                <div className={`text-2xl ${m.val ? 'text-green-400' : 'text-red-400'}`}>{m.val ? '✓' : '✗'}</div>
                <div className="text-slate-500 text-xs mt-1">{m.label}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Principle alignment */}
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-5">Leadership Principle Alignment</h3>
          <div className="space-y-4">
            {fitResult.principle_alignment.map((p, i) => (
              <div key={i}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300 font-medium">{p.principle}</span>
                  <span className="text-white font-bold">{Math.round(p.score * 100)}%</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden mb-1">
                  <div className="h-full rounded-full transition-all duration-700"
                       style={{ width: `${p.score * 100}%`, background: p.score >= 0.7 ? '#10b981' : p.score >= 0.5 ? '#f59e0b' : '#ef4444' }} />
                </div>
                <p className="text-slate-500 text-xs">{p.evidence}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Feedback */}
        <div className="glass-card p-6">
          <h3 className="text-sm font-bold text-white mb-3">Detailed Feedback</h3>
          <p className="text-slate-300 text-sm leading-relaxed mb-5">{fitResult.feedback}</p>
          <div className="p-4 rounded-xl bg-brand-500/10 border border-brand-500/20">
            <div className="text-xs text-brand-400 font-bold mb-2">💡 What would impress them more</div>
            <p className="text-slate-300 text-sm">{fitResult.what_would_impress_them_more}</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button onClick={() => { setPhase('question'); setAnswer(''); setFitResult(null) }}
                  className="btn-primary flex-1 py-3">
            Try Another Question
          </button>
          <button onClick={() => setPhase('select')} className="btn-ghost px-6">Switch Company</button>
        </div>
      </div>
    )
  }

  return null
}
