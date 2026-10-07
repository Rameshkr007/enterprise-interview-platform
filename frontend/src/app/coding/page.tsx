'use client'
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useRouter } from 'next/navigation'
import { api } from '@/lib/api'
import Link from 'next/link'

type Language = 'python' | 'javascript' | 'typescript' | 'java' | 'cpp' | 'go' | 'sql'

interface Challenge {
  challenge_id: string
  title: string
  description: string
  difficulty: string
  language: string
  starter_code: string
  constraints: string[]
  hints: string[]
  test_cases: Array<{ input: string; expected_output: string }>
  time_limit_minutes: number
  examples: Array<{ input: string; output: string; explanation: string }>
  tags: string[]
}

interface ReviewResult {
  score: number
  correctness_score: number
  efficiency_score: number
  readability_score: number
  best_practices_score: number
  time_complexity: string
  space_complexity: string
  bugs_found: Array<{ line: number; issue: string; severity: string; fix: string }>
  improvements: string[]
  strengths: string[]
  overall_feedback: string
  would_pass_interview: boolean
  model_solution: string
}

const LANG_MAP: Record<Language, string> = {
  python: 'Python 3',
  javascript: 'JavaScript',
  typescript: 'TypeScript',
  java: 'Java 21',
  cpp: 'C++ 17',
  go: 'Go 1.22',
  sql: 'SQL (PostgreSQL)',
}

export default function CodingInterviewPage() {
  const [sessionId] = useState<string>('') // Set from URL params in real usage
  const [difficulty, setDifficulty] = useState<'easy' | 'medium' | 'hard'>('medium')
  const [language, setLanguage] = useState<Language>('python')
  const [topicHint, setTopicHint] = useState('')
  const [challenge, setChallenge] = useState<Challenge | null>(null)
  const [code, setCode] = useState('')
  const [review, setReview] = useState<ReviewResult | null>(null)
  const [revealedHints, setRevealedHints] = useState<string[]>([])
  const [hintIndex, setHintIndex] = useState(0)
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const router = useRouter()

  async function generateChallenge() {
    setIsGenerating(true)
    setReview(null)
    setRevealedHints([])
    setHintIndex(0)
    try {
      const res = await api.post<Challenge>('/coding/generate', {
        session_id: sessionId || '00000000-0000-0000-0000-000000000001',
        difficulty,
        language,
        topic_hint: topicHint || null,
      })
      setChallenge(res.data)
      setCode(res.data.starter_code)
    } catch (e) {
      console.error(e)
    } finally {
      setIsGenerating(false)
    }
  }

  async function submitCode() {
    if (!challenge || !code.trim()) return
    setIsSubmitting(true)
    try {
      const res = await api.post<ReviewResult>('/coding/submit', {
        challenge_id: challenge.challenge_id,
        code,
        language,
      })
      setReview(res.data)
    } catch (e) {
      console.error(e)
    } finally {
      setIsSubmitting(false)
    }
  }

  async function revealHint() {
    if (!challenge) return
    try {
      const res = await api.get(`/coding/hint/${challenge.challenge_id}?hint_index=${hintIndex}`)
      if (res.data.hint) {
        setRevealedHints((h) => [...h, res.data.hint])
        setHintIndex((i) => i + 1)
      }
    } catch {}
  }

  return (
    <div className="min-h-screen animate-fade-in">
      <header className="border-b border-white/5 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="btn-ghost text-sm py-1.5 px-3">← Dashboard</Link>
          <span className="text-white font-semibold">💻 Coding Interview</span>
        </div>
        {challenge && (
          <div className="flex items-center gap-3">
            <span className={`badge ${difficulty === 'easy' ? 'badge-success' : difficulty === 'medium' ? 'badge-warning' : 'badge-danger'}`}>
              {difficulty}
            </span>
            <span className="text-slate-400 text-sm">{LANG_MAP[language]}</span>
          </div>
        )}
      </header>

      {!challenge ? (
        /* Setup Screen */
        <div className="max-w-lg mx-auto px-6 py-16">
          <h1 className="text-3xl font-bold text-white mb-2">Configure Coding Round</h1>
          <p className="text-slate-400 mb-10">AI generates a realistic coding challenge and evaluates your solution.</p>

          <div className="glass-card p-8 space-y-6">
            {/* Difficulty */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">Difficulty</label>
              <div className="flex gap-3">
                {(['easy', 'medium', 'hard'] as const).map((d) => (
                  <button
                    key={d}
                    onClick={() => setDifficulty(d)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize border transition-all ${
                      difficulty === d
                        ? d === 'easy' ? 'bg-green-500/20 border-green-500/50 text-green-300'
                        : d === 'medium' ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                        : 'bg-red-500/20 border-red-500/50 text-red-300'
                        : 'bg-white/5 border-white/10 text-slate-400 hover:border-white/20'
                    }`}
                  >
                    {d}
                  </button>
                ))}
              </div>
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value as Language)}
                className="input-field"
              >
                {Object.entries(LANG_MAP).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>

            {/* Topic */}
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-3">Topic Hint (optional)</label>
              <input
                className="input-field"
                placeholder="e.g. Dynamic programming, Graph traversal..."
                value={topicHint}
                onChange={(e) => setTopicHint(e.target.value)}
              />
            </div>

            <button
              id="generate-challenge-btn"
              onClick={generateChallenge}
              disabled={isGenerating}
              className="btn-primary w-full py-4 text-base"
            >
              {isGenerating ? '🤖 Generating challenge...' : '🚀 Start Coding Round'}
            </button>
          </div>
        </div>
      ) : (
        /* Split Editor View */
        <div className="flex h-[calc(100vh-57px)]">
          {/* Left: Problem */}
          <div className="w-2/5 border-r border-white/5 overflow-y-auto p-6 space-y-6">
            <div>
              <h2 className="text-xl font-bold text-white mb-2">{challenge.title}</h2>
              <div className="flex flex-wrap gap-2 mb-4">
                <span className={`badge ${difficulty === 'easy' ? 'badge-success' : difficulty === 'medium' ? 'badge-warning' : 'badge-danger'}`}>{difficulty}</span>
                {challenge.tags?.map((t) => <span key={t} className="badge badge-info text-xs">{t}</span>)}
              </div>
              <p className="text-slate-300 text-sm leading-relaxed whitespace-pre-wrap">{challenge.description}</p>
            </div>

            {/* Examples */}
            {challenge.examples?.length > 0 && (
              <div>
                <h3 className="text-sm font-bold text-white mb-3">Examples</h3>
                {challenge.examples.map((ex, i) => (
                  <div key={i} className="mb-3 p-3 rounded-lg bg-white/5 text-xs font-mono">
                    <div className="text-slate-400 mb-1">Input: <span className="text-white">{ex.input}</span></div>
                    <div className="text-slate-400 mb-1">Output: <span className="text-green-400">{ex.output}</span></div>
                    {ex.explanation && <div className="text-slate-500">// {ex.explanation}</div>}
                  </div>
                ))}
              </div>
            )}

            {/* Constraints */}
            <div>
              <h3 className="text-sm font-bold text-white mb-2">Constraints</h3>
              <ul className="space-y-1">
                {challenge.constraints.map((c, i) => (
                  <li key={i} className="text-slate-400 text-xs font-mono">• {c}</li>
                ))}
              </ul>
            </div>

            {/* Hints */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-white">Hints</h3>
                {hintIndex < (challenge.hints?.length || 0) && (
                  <button onClick={revealHint} className="text-xs text-brand-400 hover:text-brand-300">
                    Reveal hint {hintIndex + 1}
                  </button>
                )}
              </div>
              {revealedHints.map((hint, i) => (
                <div key={i} className="p-3 mb-2 rounded-lg bg-brand-500/10 border border-brand-500/20 text-slate-300 text-xs">
                  💡 {hint}
                </div>
              ))}
            </div>
          </div>

          {/* Right: Editor + Results */}
          <div className="flex-1 flex flex-col">
            {/* Code textarea (Monaco in production) */}
            <div className="flex-1 relative">
              <div className="absolute top-3 right-3 text-xs text-slate-500 font-mono">{LANG_MAP[language]}</div>
              <textarea
                id="code-editor"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                className="w-full h-full p-4 bg-slate-950 text-green-300 font-mono text-sm resize-none border-none outline-none"
                spellCheck={false}
                placeholder="Write your solution here..."
              />
            </div>

            {/* Submit bar */}
            <div className="border-t border-white/5 p-4 flex items-center gap-4">
              <button
                id="submit-code-btn"
                onClick={submitCode}
                disabled={isSubmitting || !code.trim()}
                className="btn-primary px-8 py-2"
              >
                {isSubmitting ? '⚙️ Evaluating...' : '▶ Submit Solution'}
              </button>
              <button onClick={() => { setChallenge(null); setReview(null) }} className="btn-ghost text-sm">
                New Challenge
              </button>
              {review && (
                <div className="ml-auto flex items-center gap-3">
                  <span className={`text-2xl font-bold ${review.would_pass_interview ? 'text-green-400' : 'text-red-400'}`}>
                    {review.score.toFixed(0)}%
                  </span>
                  <span className={`badge ${review.would_pass_interview ? 'badge-success' : 'badge-danger'}`}>
                    {review.would_pass_interview ? '✓ Would Pass' : '✗ Needs Work'}
                  </span>
                </div>
              )}
            </div>

            {/* Review Results */}
            {review && (
              <div className="border-t border-white/5 h-64 overflow-y-auto p-6 space-y-4">
                <div className="grid grid-cols-4 gap-3">
                  {[
                    { l: 'Correctness', v: review.correctness_score },
                    { l: 'Efficiency', v: review.efficiency_score },
                    { l: 'Readability', v: review.readability_score },
                    { l: 'Best Practices', v: review.best_practices_score },
                  ].map((s) => (
                    <div key={s.l} className="text-center">
                      <div className={`text-lg font-bold ${s.v >= 80 ? 'text-green-400' : s.v >= 60 ? 'text-amber-400' : 'text-red-400'}`}>
                        {s.v.toFixed(0)}
                      </div>
                      <div className="text-xs text-slate-500">{s.l}</div>
                    </div>
                  ))}
                </div>

                <div className="flex gap-4 text-xs text-slate-400">
                  <span>⏱ Time: <code className="text-white">{review.time_complexity}</code></span>
                  <span>📦 Space: <code className="text-white">{review.space_complexity}</code></span>
                </div>

                {review.bugs_found.length > 0 && (
                  <div>
                    <div className="text-xs font-bold text-red-400 mb-2">Bugs Found</div>
                    {review.bugs_found.map((b, i) => (
                      <div key={i} className="text-xs p-2 mb-1 rounded bg-red-500/10 text-slate-300">
                        <span className={`font-bold ${b.severity === 'critical' ? 'text-red-400' : b.severity === 'warning' ? 'text-amber-400' : 'text-slate-400'}`}>
                          [{b.severity}]
                        </span>{' '}
                        Line {b.line}: {b.issue} → {b.fix}
                      </div>
                    ))}
                  </div>
                )}

                <p className="text-slate-300 text-sm leading-relaxed">{review.overall_feedback}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
