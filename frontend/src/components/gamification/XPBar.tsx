'use client'
import { useEffect, useRef } from 'react'

interface XPBarProps {
  totalXp: number
  level: number
  title: string
  emoji: string
  progressToNext: number
  xpToNext: number
  nextTitle: string
  xpEarned?: number // Optional: animate newly earned XP
}

export function XPBar({
  totalXp, level, title, emoji, progressToNext, xpToNext, nextTitle, xpEarned
}: XPBarProps) {
  const barRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (barRef.current) {
      barRef.current.style.width = `${progressToNext}%`
    }
  }, [progressToNext])

  const levelColors = [
    '#94a3b8', '#60a5fa', '#34d399', '#f59e0b',
    '#f97316', '#ef4444', '#a855f7', '#ec4899',
    '#06b6d4', '#eab308',
  ]
  const color = levelColors[(level - 1) % levelColors.length]

  return (
    <div className="glass-card p-5 select-none">
      <div className="flex items-center gap-4 mb-4">
        {/* Level badge */}
        <div
          className="w-14 h-14 rounded-2xl flex flex-col items-center justify-center text-center flex-shrink-0 border-2"
          style={{ borderColor: color, background: `${color}20` }}
        >
          <div className="text-xl leading-none">{emoji}</div>
          <div className="text-xs font-bold mt-0.5" style={{ color }}>{level}</div>
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-white font-bold">{title}</span>
            <span className="text-slate-400 text-xs">{totalXp.toLocaleString()} XP</span>
          </div>

          {/* Progress bar */}
          <div className="h-3 bg-white/5 rounded-full overflow-hidden relative">
            <div
              ref={barRef}
              className="h-full rounded-full transition-all duration-1000 ease-out relative"
              style={{ width: '0%', background: `linear-gradient(90deg, ${color}88, ${color})` }}
            >
              {/* Shimmer */}
              <div className="absolute inset-0 overflow-hidden rounded-full">
                <div
                  className="absolute inset-y-0 w-1/3 bg-white/20"
                  style={{ animation: 'shimmer 2s infinite', left: '-33%' }}
                />
              </div>
            </div>
          </div>

          <div className="flex justify-between mt-1">
            <span className="text-xs text-slate-500">{xpToNext.toLocaleString()} XP to {nextTitle}</span>
            <span className="text-xs" style={{ color }}>{progressToNext.toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* XP earned notification */}
      {xpEarned && xpEarned > 0 && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-green-500/10 border border-green-500/20">
          <span className="text-green-400 font-bold text-sm">+{xpEarned} XP</span>
          <span className="text-slate-400 text-xs">earned this session</span>
          <span className="ml-auto text-green-400 text-xs">🎉</span>
        </div>
      )}
    </div>
  )
}

// ── Achievement Toast ────────────────────────────────────────────────────────
interface AchievementToastProps {
  achievement: { name: string; icon: string; description: string; xp_reward: number }
  onDismiss: () => void
}

export function AchievementToast({ achievement, onDismiss }: AchievementToastProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 5000)
    return () => clearTimeout(t)
  }, [onDismiss])

  return (
    <div className="fixed bottom-6 right-6 z-50 glass-card p-5 w-80 border border-yellow-500/30 bg-yellow-500/10 animate-slide-up shadow-2xl">
      <div className="flex items-start gap-4">
        <div className="text-4xl">{achievement.icon}</div>
        <div className="flex-1">
          <div className="text-xs text-yellow-400 font-bold uppercase tracking-wider mb-1">Achievement Unlocked!</div>
          <div className="text-white font-bold">{achievement.name}</div>
          <div className="text-slate-400 text-xs mt-1">{achievement.description}</div>
          <div className="text-yellow-400 text-xs mt-2 font-medium">+{achievement.xp_reward} XP</div>
        </div>
        <button onClick={onDismiss} className="text-slate-500 hover:text-white text-xs">✕</button>
      </div>
    </div>
  )
}
