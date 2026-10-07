'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useQuery, useMutation } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { useAuthStore } from '@/store/auth'
import Link from 'next/link'

interface Improvement {
  improved_summary: string
  bullet_improvements: Array<{ original: string; improved: string; reason: string }>
  missing_keywords: string[]
  skills_to_highlight: string[]
  format_suggestions: string[]
  ats_optimization_tips: string[]
  estimated_score_improvement: number
}

interface Roadmap {
  current_level: string
  target_role: string
  timeline_months: number
  skill_roadmap: Array<{
    skill: string
    priority: string
    resources: Array<{ title: string; url: string; type: string }>
    estimated_weeks: number
  }>
  certifications: Array<{ name: string; provider: string; url: string; value: string }>
  salary_range: { min: number; max: number; currency: string }
  job_titles_to_target: string[]
  networking_tips: string[]
}

type Tab = 'improve' | 'roadmap' | 'coaching'

export default function ResumeBuilderPage() {
  const { user } = useAuthStore()
  const [tab, setTab] = useState<Tab>('improve')
  const [targetRole, setTargetRole] = useState('')
  const [improvement, setImprovement] = useState<Improvement | null>(null)
  const [roadmap, setRoadmap] = useState<Roadmap | null>(null)
  const [coaching, setCoaching] = useState<Record<string, unknown> | null>(null)
  const router = useRouter()

  // For demo, we assume the user's first resume/ATS analysis IDs
  // In production, user selects from a list
  const [resumeId, setResumeId] = useState<string>('')
  const [atsId, setAtsId] = useState<string>('')

  // Fetch user's resumes
  const { data: resumes } = useQuery({
    queryKey: ['resumes'],
    queryFn: () => api.get('/ats/resume').then((r) => r.data),
    enabled: !!user,
  })

  const improveMutation = useMutation({
    mutationFn: () =>
      api.post('/resume-builder/improve', { resume_id: resumeId, ats_analysis_id: atsId || null })
         .then((r) => r.data),
    onSuccess: (data) => setImprovement(data),
  })

  const roadmapMutation = useMutation({
    mutationFn: () =>
      api.post('/resume-builder/career-roadmap', {
        resume_id: resumeId,
        target_role: targetRole,
        ats_analysis_id: atsId || null,
      }).then((r) => r.data),
    onSuccess: (data) => setRoadmap(data),
  })

  const coachingMutation = useMutation({
    mutationFn: () => api.get('/analytics/coaching').then((r) => r.data),
    onSuccess: (data) => setCoaching(data),
  })

  const tabs: { id: Tab; label: string; icon: string }[] = [
    { id: 'improve', label: 'AI Resume Rewriter', icon: '✍️' },
    { id: 'roadmap', label: 'Career Roadmap', icon: '🗺️' },
    { id: 'coaching', label: 'Interview Coach', icon: '🎓' },
  ]

  return (
    <div className="min-h-screen max-w-5xl mx-auto px-6 py-12 animate-fade-in">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white mb-1">AI Career Intelligence</h1>
          <p className="text-slate-400 text-sm">Resume optimization, career roadmap & interview coaching</p>
        </div>
        <Link href="/dashboard" className="btn-ghost">← Dashboard</Link>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-8 p-1 bg-white/5 rounded-xl w-fit">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-all ${
              tab === t.id
                ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/30'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <span>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Resume Selector */}
      <div className="glass-card p-5 mb-6 flex flex-wrap gap-4">
        <div className="flex-1 min-w-48">
          <label className="block text-xs text-slate-500 mb-1">Resume ID</label>
          <input
            className="input-field text-sm py-2"
            placeholder="paste-resume-uuid"
            value={resumeId}
            onChange={(e) => setResumeId(e.target.value)}
          />
        </div>
        <div className="flex-1 min-w-48">
          <label className="block text-xs text-slate-500 mb-1">ATS Analysis ID (optional)</label>
          <input
            className="input-field text-sm py-2"
            placeholder="paste-ats-analysis-uuid"
            value={atsId}
            onChange={(e) => setAtsId(e.target.value)}
          />
        </div>
      </div>

      {/* ─── Tab: Improve ─────────────────────────────────── */}
      {tab === 'improve' && (
        <div className="space-y-6">
          <button
            id="improve-resume-btn"
            onClick={() => improveMutation.mutate()}
            disabled={!resumeId || improveMutation.isPending}
            className="btn-primary w-full py-4"
          >
            {improveMutation.isPending ? '✨ Rewriting with AI...' : '✨ Generate AI Improvements'}
          </button>

          {improvement && (
            <div className="space-y-6 animate-fade-in">
              {/* New Summary */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-bold text-brand-400 uppercase tracking-wide mb-3">Improved Summary</h3>
                <p className="text-slate-200 leading-relaxed text-sm">{improvement.improved_summary}</p>
              </div>

              {/* Est. Score Boost */}
              <div className="glass-card p-5 flex items-center gap-4">
                <div className="text-4xl font-bold text-green-400">
                  +{improvement.estimated_score_improvement.toFixed(0)}
                </div>
                <div>
                  <div className="text-white font-semibold">Estimated ATS Score Improvement</div>
                  <div className="text-slate-400 text-sm">After applying all suggestions</div>
                </div>
              </div>

              {/* Bullet improvements */}
              <div className="glass-card p-6">
                <h3 className="text-sm font-bold text-white mb-4">Bullet Point Rewrites</h3>
                <div className="space-y-5">
                  {improvement.bullet_improvements.map((b, i) => (
                    <div key={i} className="border-l-2 border-brand-500/30 pl-4">
                      <div className="text-red-400 text-xs font-medium mb-1 line-through opacity-60">{b.original}</div>
                      <div className="text-green-400 text-sm font-medium mb-1">{b.improved}</div>
                      <div className="text-slate-500 text-xs">💡 {b.reason}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Keywords + Tips */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-bold text-white mb-3">Missing ATS Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {improvement.missing_keywords.map((kw) => (
                      <span key={kw} className="px-2 py-1 bg-red-500/10 border border-red-500/20 text-red-300 text-xs rounded-lg">{kw}</span>
                    ))}
                  </div>
                </div>
                <div className="glass-card p-5">
                  <h3 className="text-sm font-bold text-white mb-3">ATS Optimization Tips</h3>
                  <ul className="space-y-2">
                    {improvement.ats_optimization_tips.map((tip, i) => (
                      <li key={i} className="text-slate-300 text-xs flex gap-2">
                        <span className="text-brand-400">→</span>{tip}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ─── Tab: Roadmap ─────────────────────────────────── */}
      {tab === 'roadmap' && (
        <div className="space-y-6">
          <div className="glass-card p-5 flex gap-4">
            <input
              className="input-field flex-1"
              placeholder="Target role (e.g. Senior ML Engineer)"
              value={targetRole}
              onChange={(e) => setTargetRole(e.target.value)}
            />
            <button
              id="generate-roadmap-btn"
              onClick={() => roadmapMutation.mutate()}
              disabled={!resumeId || !targetRole || roadmapMutation.isPending}
              className="btn-primary px-6"
            >
              {roadmapMutation.isPending ? 'Generating...' : 'Generate'}
            </button>
          </div>

          {roadmap && (
            <div className="space-y-6 animate-fade-in">
              {/* Header */}
              <div className="glass-card p-6 flex items-center justify-between">
                <div>
                  <div className="text-slate-400 text-sm mb-1">{roadmap.current_level} → {roadmap.target_role}</div>
                  <div className="text-2xl font-bold text-white">{roadmap.timeline_months} months</div>
                  <div className="text-slate-400 text-sm">estimated timeline</div>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-bold text-green-400">
                    \${roadmap.salary_range.min.toLocaleString()}–\${roadmap.salary_range.max.toLocaleString()}
                  </div>
                  <div className="text-slate-400 text-sm">{roadmap.salary_range.currency} salary range</div>
                </div>
              </div>

              {/* Skill Roadmap */}
              <div className="glass-card p-6">
                <h3 className="text-lg font-bold text-white mb-5">Learning Roadmap</h3>
                <div className="space-y-6">
                  {roadmap.skill_roadmap.map((item, i) => (
                    <div key={i} className="flex gap-4">
                      <div className={`w-2 rounded-full self-stretch ${
                        item.priority === 'high' ? 'bg-red-400' :
                        item.priority === 'medium' ? 'bg-amber-400' : 'bg-green-400'
                      }`} />
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-white font-semibold">{item.skill}</span>
                          <div className="flex items-center gap-2">
                            <span className={`badge text-xs ${item.priority === 'high' ? 'badge-danger' : item.priority === 'medium' ? 'badge-warning' : 'badge-success'}`}>
                              {item.priority}
                            </span>
                            <span className="text-slate-500 text-xs">{item.estimated_weeks}w</span>
                          </div>
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {item.resources.map((r, j) => (
                            <a key={j} href={r.url} target="_blank" rel="noopener noreferrer"
                               className="text-xs text-brand-400 hover:text-brand-300 underline">
                              {r.type === 'course' ? '📚' : r.type === 'book' ? '📖' : '🔗'} {r.title}
                            </a>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Certifications */}
              {roadmap.certifications.length > 0 && (
                <div className="glass-card p-6">
                  <h3 className="text-lg font-bold text-white mb-4">Recommended Certifications</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {roadmap.certifications.map((cert, i) => (
                      <div key={i} className="p-4 rounded-xl bg-white/5">
                        <div className="text-white font-medium mb-1">{cert.name}</div>
                        <div className="text-slate-400 text-sm mb-2">{cert.provider} • {cert.value}</div>
                        <a href={cert.url} target="_blank" rel="noopener noreferrer"
                           className="text-brand-400 text-xs hover:underline">Learn more →</a>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* ─── Tab: Coaching ─────────────────────────────────── */}
      {tab === 'coaching' && (
        <div className="space-y-6">
          <button
            id="get-coaching-btn"
            onClick={() => coachingMutation.mutate()}
            disabled={coachingMutation.isPending}
            className="btn-primary w-full py-4"
          >
            {coachingMutation.isPending ? '🎓 Analyzing your sessions...' : '🎓 Generate AI Coaching Plan'}
          </button>

          {coaching && (
            <div className="space-y-6 animate-fade-in">
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-bold text-white">Interview Readiness</h3>
                  <div className="text-3xl font-bold text-brand-400">
                    {((coaching.overall_readiness_score as number) * 100).toFixed(0)}%
                  </div>
                </div>
                <p className="text-slate-300 text-sm leading-relaxed">{coaching.pattern_analysis as string}</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="glass-card p-5">
                  <h3 className="text-sm font-bold text-red-400 mb-4">Areas to Improve</h3>
                  {(coaching.top_weaknesses as Array<{area: string; evidence: string; fix: string}>).map((w, i) => (
                    <div key={i} className="mb-4 pb-4 border-b border-white/5 last:border-0">
                      <div className="text-white font-medium mb-1">{w.area}</div>
                      <div className="text-slate-400 text-xs mb-2">{w.evidence}</div>
                      <div className="text-green-400 text-xs">Fix: {w.fix}</div>
                    </div>
                  ))}
                </div>
                <div className="glass-card p-5">
                  <h3 className="text-sm font-bold text-green-400 mb-4">Your Strengths</h3>
                  {(coaching.top_strengths as Array<{area: string; evidence: string}>).map((s, i) => (
                    <div key={i} className="mb-4 pb-4 border-b border-white/5 last:border-0">
                      <div className="text-white font-medium mb-1">{s.area}</div>
                      <div className="text-slate-400 text-xs">{s.evidence}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="glass-card p-6">
                <h3 className="text-lg font-bold text-white mb-4">Practice Scenarios</h3>
                <div className="space-y-4">
                  {(coaching.practice_scenarios as Array<{scenario: string; model_answer_outline: string}>).map((ps, i) => (
                    <div key={i} className="p-4 rounded-xl bg-white/5">
                      <div className="text-white font-medium mb-2">Scenario {i+1}: {ps.scenario}</div>
                      <div className="text-slate-400 text-sm">{ps.model_answer_outline}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
