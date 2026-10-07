'use client'
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import Link from 'next/link'

const STATUS_COLUMNS = [
  { key: 'wishlist',     label: '⭐ Wishlist',      color: 'border-slate-500/30 bg-slate-500/5' },
  { key: 'applied',      label: '📤 Applied',        color: 'border-blue-500/30 bg-blue-500/5' },
  { key: 'phone_screen', label: '📞 Phone Screen',   color: 'border-purple-500/30 bg-purple-500/5' },
  { key: 'technical',    label: '💻 Technical',      color: 'border-yellow-500/30 bg-yellow-500/5' },
  { key: 'final_round',  label: '🏁 Final Round',    color: 'border-orange-500/30 bg-orange-500/5' },
  { key: 'offer',        label: '🎉 Offer',          color: 'border-green-500/30 bg-green-500/5' },
  { key: 'rejected',     label: '❌ Rejected',       color: 'border-red-500/30 bg-red-500/5' },
]

const PRIORITY_COLORS = { 1: 'text-red-400', 2: 'text-amber-400', 3: 'text-slate-500' }
const PRIORITY_LABELS = { 1: '🔴 High', 2: '🟡 Medium', 3: '⚪ Low' }

interface Application {
  id: string
  company_name: string
  role_title: string
  status: string
  location: string | null
  is_remote: boolean
  salary_range: string | null
  tags: string[]
  priority: 1 | 2 | 3
  contact_name: string | null
  notes: string | null
  follow_up_at: string | null
  applied_at: string | null
  timeline: Array<{ status: string; timestamp: string }>
  job_url: string | null
}

interface AddModalProps {
  onClose: () => void
  onSave: (data: Record<string, unknown>) => void
}

function AddModal({ onClose, onSave }: AddModalProps) {
  const [form, setForm] = useState({
    company_name: '', role_title: '', job_url: '',
    status: 'wishlist', location: '', is_remote: false,
    salary_min: '', salary_max: '', notes: '', priority: 2,
  })
  function upd(k: string) {
    return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
      setForm(f => ({ ...f, [k]: e.target.value }))
  }
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="glass-card p-8 w-full max-w-lg mx-4 animate-fade-in">
        <h2 className="text-xl font-bold text-white mb-6">Add Application</h2>
        <div className="space-y-4">
          <input className="input-field" placeholder="Company name *" value={form.company_name} onChange={upd('company_name')} />
          <input className="input-field" placeholder="Role title *" value={form.role_title} onChange={upd('role_title')} />
          <input className="input-field" placeholder="Job URL" value={form.job_url} onChange={upd('job_url')} />
          <div className="grid grid-cols-2 gap-3">
            <select className="input-field" value={form.status} onChange={upd('status')}>
              {STATUS_COLUMNS.map(s => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
            <select className="input-field" value={form.priority} onChange={upd('priority')}>
              <option value={1}>🔴 High</option>
              <option value={2}>🟡 Medium</option>
              <option value={3}>⚪ Low</option>
            </select>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <input className="input-field" placeholder="Min salary ($)" type="number" value={form.salary_min} onChange={upd('salary_min')} />
            <input className="input-field" placeholder="Max salary ($)" type="number" value={form.salary_max} onChange={upd('salary_max')} />
          </div>
          <input className="input-field" placeholder="Location" value={form.location} onChange={upd('location')} />
          <textarea className="input-field resize-none" rows={3} placeholder="Notes" value={form.notes} onChange={upd('notes')} />
        </div>
        <div className="flex gap-3 mt-6">
          <button
            onClick={() => onSave({
              ...form,
              salary_min: form.salary_min ? Number(form.salary_min) : null,
              salary_max: form.salary_max ? Number(form.salary_max) : null,
              priority: Number(form.priority),
            })}
            disabled={!form.company_name || !form.role_title}
            className="btn-primary flex-1 py-3"
          >
            Add Application
          </button>
          <button onClick={onClose} className="btn-ghost px-6">Cancel</button>
        </div>
      </div>
    </div>
  )
}

function AppCard({ app, onMove }: { app: Application; onMove: (id: string, status: string) => void }) {
  const [expanded, setExpanded] = useState(false)
  const nextStatuses = STATUS_COLUMNS.filter(s => s.key !== app.status && s.key !== 'rejected')

  return (
    <div className="p-4 rounded-xl bg-white/5 border border-white/8 hover:border-white/15 transition-all cursor-pointer group" onClick={() => setExpanded(!expanded)}>
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex-1 min-w-0">
          <div className="text-white font-semibold text-sm truncate">{app.company_name}</div>
          <div className="text-slate-400 text-xs truncate">{app.role_title}</div>
        </div>
        <span className={`text-xs font-medium ${PRIORITY_COLORS[app.priority as 1|2|3]}`}>
          {['🔴','🟡','⚪'][app.priority - 1]}
        </span>
      </div>

      <div className="flex flex-wrap gap-1.5 mb-3">
        {app.salary_range && <span className="text-xs text-green-400 bg-green-500/10 px-2 py-0.5 rounded">{app.salary_range}</span>}
        {app.is_remote && <span className="text-xs text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded">Remote</span>}
        {app.location && !app.is_remote && <span className="text-xs text-slate-400">📍 {app.location}</span>}
      </div>

      {app.follow_up_at && (
        <div className="text-xs text-amber-400 mb-2">
          🔔 Follow up {new Date(app.follow_up_at).toLocaleDateString()}
        </div>
      )}

      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/5 space-y-3 animate-fade-in">
          {app.notes && <p className="text-slate-400 text-xs">{app.notes}</p>}
          {app.contact_name && <div className="text-xs text-slate-400">👤 {app.contact_name}</div>}
          {app.job_url && (
            <a href={app.job_url} target="_blank" rel="noopener noreferrer"
               className="text-brand-400 text-xs hover:underline" onClick={e => e.stopPropagation()}>
              🔗 View Job Posting
            </a>
          )}

          {/* Status timeline */}
          {app.timeline.length > 0 && (
            <div className="space-y-1">
              <div className="text-xs text-slate-500 font-medium">Timeline</div>
              {app.timeline.map((t, i) => (
                <div key={i} className="flex gap-2 text-xs">
                  <span className="text-slate-500">{new Date(t.timestamp).toLocaleDateString()}</span>
                  <span className="text-slate-300 capitalize">{t.status.replace('_', ' ')}</span>
                </div>
              ))}
            </div>
          )}

          {/* Quick move */}
          <div className="flex flex-wrap gap-1.5" onClick={e => e.stopPropagation()}>
            {nextStatuses.slice(0, 4).map(s => (
              <button key={s.key} onClick={() => onMove(app.id, s.key)}
                      className="text-xs px-2 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all">
                → {s.label.split(' ')[1]}
              </button>
            ))}
            <button onClick={() => onMove(app.id, 'rejected')}
                    className="text-xs px-2 py-1 rounded bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-all">
              Reject
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function JobTrackerPage() {
  const [showModal, setShowModal] = useState(false)
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['job-tracker'],
    queryFn: () => api.get('/job-tracker').then(r => r.data),
  })

  const addMutation = useMutation({
    mutationFn: (body: Record<string, unknown>) => api.post('/job-tracker', body),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['job-tracker'] }); setShowModal(false) },
  })

  const moveMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      api.patch(`/job-tracker/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['job-tracker'] }),
  })

  const kanban: Record<string, Application[]> = data?.kanban ?? {}
  const stats = data?.stats ?? {}

  return (
    <div className="min-h-screen animate-fade-in">
      {/* Header */}
      <div className="border-b border-white/5 px-6 py-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">💼 Job Application Tracker</h1>
          <div className="flex gap-4 mt-1">
            <span className="text-slate-400 text-sm">Total: <b className="text-white">{stats.total ?? 0}</b></span>
            <span className="text-slate-400 text-sm">Active: <b className="text-blue-400">{stats.active ?? 0}</b></span>
            <span className="text-slate-400 text-sm">Offers: <b className="text-green-400">{stats.offers ?? 0}</b></span>
            <span className="text-slate-400 text-sm">Rejected: <b className="text-red-400">{stats.rejections ?? 0}</b></span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="btn-ghost text-sm">← Dashboard</Link>
          <button
            id="add-application-btn"
            onClick={() => setShowModal(true)}
            className="btn-primary"
          >
            + Add Application
          </button>
        </div>
      </div>

      {/* Kanban board */}
      {isLoading ? (
        <div className="flex gap-4 p-6 overflow-x-auto">
          {STATUS_COLUMNS.map(c => (
            <div key={c.key} className="skeleton w-64 h-96 rounded-xl flex-shrink-0" />
          ))}
        </div>
      ) : (
        <div className="flex gap-4 p-6 overflow-x-auto min-h-[calc(100vh-120px)]">
          {STATUS_COLUMNS.map(col => {
            const apps = kanban[col.key] ?? []
            return (
              <div key={col.key} className={`flex-shrink-0 w-72 rounded-2xl border p-4 ${col.color}`}>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-bold text-white">{col.label}</h3>
                  <span className="text-xs text-slate-400 bg-white/10 px-2 py-0.5 rounded-full">{apps.length}</span>
                </div>
                <div className="space-y-3">
                  {apps.map(app => (
                    <AppCard
                      key={app.id}
                      app={app}
                      onMove={(id, status) => moveMutation.mutate({ id, status })}
                    />
                  ))}
                  {apps.length === 0 && (
                    <div className="text-center text-slate-600 text-xs py-8">Empty</div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {showModal && (
        <AddModal
          onClose={() => setShowModal(false)}
          onSave={(data) => addMutation.mutate(data)}
        />
      )}
    </div>
  )
}
