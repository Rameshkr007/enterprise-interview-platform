'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { interviewApi } from '@/lib/api'
import { useInterviewStore } from '@/store/interview'

export default function NewInterviewPage() {
  const [count, setCount] = useState(10)
  const [categories, setCategories] = useState<string[]>([])
  const [isCreating, setIsCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const setSession = useInterviewStore((s) => s.setSession)
  const router = useRouter()

  const allCategories = ['behavioral', 'technical', 'system_design', 'situational', 'culture_fit']

  function toggleCategory(cat: string) {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat]
    )
  }

  async function startInterview() {
    setIsCreating(true)
    setError(null)
    try {
      const session = await interviewApi.createSession({
        target_question_count: count,
        focus_categories: categories,
        adaptive_mode: true,
      })
      setSession(session)
      router.push(`/interview/${session.id}`)
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { message?: string } } })?.response?.data?.message ?? 'Failed to start session'
      setError(msg)
      setIsCreating(false)
    }
  }

  return (
    <div className="min-h-screen max-w-2xl mx-auto px-6 py-16 animate-fade-in">
      <button onClick={() => router.push('/dashboard')} className="btn-ghost mb-8">
        &larr; Dashboard
      </button>
      <h1 className="text-3xl font-bold text-white mb-2">Configure Interview Session</h1>
      <p className="text-slate-400 mb-10">The AI adapts difficulty in real-time based on your answers.</p>

      {error && (
        <div className="p-4 mb-6 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">{error}</div>
      )}

      <div className="glass-card p-8 space-y-8">
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-4">
            Number of Questions: <span className="text-brand-400">{count}</span>
          </label>
          <input
            id="question-count"
            type="range" min={3} max={20} value={count}
            onChange={(e) => setCount(Number(e.target.value))}
            className="w-full accent-brand-500"
          />
          <div className="flex justify-between text-xs text-slate-500 mt-1">
            <span>3</span><span>20</span>
          </div>
        </div>

        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-4">Focus Categories (optional)</label>
          <div className="flex flex-wrap gap-3">
            {allCategories.map((cat) => (
              <button
                key={cat}
                id={`cat-${cat}`}
                onClick={() => toggleCategory(cat)}
                className={`px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                  categories.includes(cat)
                    ? 'bg-brand-500/20 border-brand-500/50 text-brand-300'
                    : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                }`}
              >
                {cat.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <button
          id="start-interview-btn"
          onClick={startInterview}
          disabled={isCreating}
          className="btn-primary w-full py-4 text-base"
        >
          {isCreating ? 'Initializing AI Interviewer...' : 'Start Interview'}
        </button>
      </div>
    </div>
  )
}
