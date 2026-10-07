'use client'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'
import { useState } from 'react'

interface DailyChallenge {
  challenge_date: string
  category: string
  difficulty: string
  xp_reward: number
  streak_bonus_xp: number
  expires_at: string
}

interface ReviewItem {
  turn_id: string
  question_text: string
  category: string
  difficulty: string
  last_score: number
  due_date: string
  review_reason: string
}

export default function DailyChallengePage() {
  const [practiceAnswer, setPracticeAnswer] = useState('')
  const [practicingId, setPracticingId] = useState<string | null>(null)
  const [reviewScores, setReviewScores] = useState<Record<string, 'easy' | 'good' | 'hard'>>({})

  const { data: challenge } = useQuery<DailyChallenge>({
    queryKey: ['daily-challenge'],
    queryFn: () => api.get('/game/daily-challenge').then(r => r.data),
  })

  const { data: reviewData } = useQuery<{ due_count: number; review_items: ReviewItem[]; estimated_minutes: number }>({
    queryKey: ['review-queue'],
    queryFn: () => api.get('/game/review-queue').then(r => r.data),
  })

  const { data: levels } = useQuery({
    queryKey: ['levels'],
    queryFn: () => api.get('/game/levels').then(r => r.data),
  })

  const diffColor = (d: string) =>
    d === 'hard' ? 'text-red-400 bg-red-500/10' :
    d === 'medium' ? 'text-amber-400 bg-amber-500/10' : 'text-green-400 bg-green-500/10'

  const catEmoji: Record<string, string> = {
    behavioral: '🧠', technical: '⚙️', system_design: '🏗️',
    situational: '🎭', culture_fit: '🤝', domain_specific: '📚',
  }

  return (
    <div className="min-h-screen max-w-5xl mx-auto px-6 py-12 animate-fade-in space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">🔥 Daily Practice</h1>
          <p className="text-slate-400 text-sm">Daily challenge + spaced repetition review queue</p>
        </div>
        <Link href="/dashboard" className="btn-ghost">← Dashboard</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Daily Challenge Card */}
        <div className="lg:col-span-2">
          {challenge ? (
            <div className="glass-card p-8 relative overflow-hidden">
              {/* Decorative glow */}
              <div className="absolute -top-10 -right-10 w-40 h-40 bg-brand-500/10 rounded-full blur-3xl pointer-events-none" />

              <div className="flex items-center gap-3 mb-6">
                <div className="w-12 h-12 rounded-2xl bg-brand-500/20 flex items-center justify-center text-2xl">
                  {catEmoji[challenge.category] ?? '❓'}
                </div>
                <div>
                  <div className="text-xs text-brand-400 font-bold uppercase tracking-wider">Daily Challenge</div>
                  <div className="text-white font-bold capitalize">{challenge.category.replace('_', ' ')}</div>
                </div>
                <div className="ml-auto text-right">
                  <div className={`text-xs px-2 py-1 rounded capitalize font-medium ${diffColor(challenge.difficulty)}`}>
                    {challenge.difficulty}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 mb-6">
                <div className="text-center flex-1">
                  <div className="text-2xl font-bold text-brand-400">+{challenge.xp_reward}</div>
                  <div className="text-xs text-slate-500">Base XP</div>
                </div>
                <div className="text-slate-600">+</div>
                <div className="text-center flex-1">
                  <div className="text-2xl font-bold text-amber-400">+{challenge.streak_bonus_xp}</div>
                  <div className="text-xs text-slate-500">Streak bonus</div>
                </div>
                <div className="text-slate-600">=</div>
                <div className="text-center flex-1">
                  <div className="text-2xl font-bold text-green-400">+{challenge.xp_reward + challenge.streak_bonus_xp}</div>
                  <div className="text-xs text-slate-500">Total XP</div>
                </div>
              </div>

              <div className="text-xs text-slate-500 mb-5">
                Expires: {new Date(challenge.expires_at).toLocaleTimeString()} tonight
              </div>

              <Link
                href={`/interview/new?mode=daily&category=${challenge.category}&difficulty=${challenge.difficulty}`}
                className="btn-primary w-full py-4 text-center block"
              >
                🚀 Start Today's Challenge
              </Link>
            </div>
          ) : (
            <div className="skeleton h-64 rounded-2xl" />
          )}
        </div>

        {/* Review Queue */}
        <div>
          <div className="glass-card p-6 h-full">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-white">📚 Review Queue</h3>
              {reviewData && (
                <span className="text-xs bg-amber-500/20 text-amber-400 px-2 py-1 rounded-full font-bold">
                  {reviewData.due_count} due
                </span>
              )}
            </div>

            {reviewData && reviewData.due_count > 0 ? (
              <>
                <div className="text-xs text-slate-500 mb-4">
                  ~{reviewData.estimated_minutes} min to complete all reviews
                </div>
                <div className="space-y-3 max-h-72 overflow-y-auto pr-1">
                  {reviewData.review_items.map(item => (
                    <div key={item.turn_id} className="p-3 rounded-xl bg-white/5 border border-white/8">
                      <div className="text-slate-300 text-xs leading-relaxed line-clamp-2 mb-2">
                        {item.question_text}
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-1.5 py-0.5 rounded capitalize ${diffColor(item.difficulty)}`}>
                            {item.difficulty}
                          </span>
                          <span className="text-xs text-slate-500">Last: {item.last_score}%</span>
                        </div>
                        <div className="flex gap-1">
                          {['easy', 'good', 'hard'].map(rating => (
                            <button
                              key={rating}
                              onClick={() => setReviewScores(s => ({ ...s, [item.turn_id]: rating as 'easy' | 'good' | 'hard' }))}
                              className={`text-xs px-2 py-0.5 rounded transition-all ${
                                reviewScores[item.turn_id] === rating
                                  ? rating === 'easy' ? 'bg-green-500/30 text-green-300'
                                  : rating === 'good' ? 'bg-blue-500/30 text-blue-300'
                                  : 'bg-red-500/30 text-red-300'
                                  : 'bg-white/5 text-slate-500 hover:text-white'
                              }`}
                            >
                              {rating}
                            </button>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">✅</div>
                <div className="text-white font-medium mb-1">All caught up!</div>
                <div className="text-slate-500 text-sm">No reviews due today</div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Level progression table */}
      {levels && (
        <div className="glass-card p-6">
          <h3 className="text-lg font-bold text-white mb-5">🏆 Level Progression</h3>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
            {(levels as Array<{level: number; title: string; emoji: string; xp_required: number}>).map(l => (
              <div key={l.level} className="text-center p-3 rounded-xl bg-white/5 border border-white/8">
                <div className="text-2xl mb-1">{l.emoji}</div>
                <div className="text-white text-xs font-bold">{l.title}</div>
                <div className="text-slate-500 text-xs mt-0.5">{l.xp_required.toLocaleString()} XP</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
