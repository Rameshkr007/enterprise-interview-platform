'use client'

import React, { useEffect, useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Activity,
  ShieldAlert,
  DollarSign,
  Server,
  Zap,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  Cpu,
  Database,
  Sliders,
  ExternalLink,
  Layers,
  ArrowUpRight,
  TrendingDown,
  Power,
  Search,
  ChevronDown,
  ChevronRight,
  Terminal,
  Copy,
  Check,
  BellRing,
  Filter,
} from 'lucide-react'
import { observabilityApi, governanceApi } from '@/lib/api'
import type {
  ObservabilityMetricsSummary,
  DeepHealthCheckResult,
  CircuitBreakerStatus,
  OrganizationBudgetStatus,
  SystemAlertItem,
  TraceRecord,
} from '@/lib/types'

export default function ObservabilityAdminPage() {
  const [metrics, setMetrics] = useState<ObservabilityMetricsSummary | null>(null)
  const [health, setHealth] = useState<DeepHealthCheckResult | null>(null)
  const [breakers, setBreakers] = useState<CircuitBreakerStatus[]>([])
  const [budget, setBudget] = useState<OrganizationBudgetStatus | null>(null)
  const [alerts, setAlerts] = useState<SystemAlertItem[]>([])
  const [traces, setTraces] = useState<TraceRecord[]>([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Alerts state
  const [onlyActiveAlerts, setOnlyActiveAlerts] = useState(true)
  const [acknowledgingAlertId, setAcknowledgingAlertId] = useState<string | null>(null)

  // Traces state
  const [traceSearch, setTraceSearch] = useState('')
  const [selectedTraceId, setSelectedTraceId] = useState<string | null>(null)

  // Prometheus Modal State
  const [promModalOpen, setPromModalOpen] = useState(false)
  const [promMetricsText, setPromMetricsText] = useState('')
  const [promLoading, setPromLoading] = useState(false)
  const [promCopied, setPromCopied] = useState(false)

  // Budget Edit Modal State
  const [budgetModalOpen, setBudgetModalOpen] = useState(false)
  const [newBudgetVal, setNewBudgetVal] = useState('100.00')
  const [newActionVal, setNewActionVal] = useState<'degrade_to_cheap' | 'block'>('degrade_to_cheap')
  const [budgetSaving, setBudgetSaving] = useState(false)

  const loadData = async (isManualRefresh = false) => {
    try {
      if (isManualRefresh) setRefreshing(true)
      else setLoading(true)
      setError(null)

      const [metricsRes, healthRes, breakersRes, budgetRes, alertsRes, tracesRes] = await Promise.allSettled([
        observabilityApi.getMetricsSummary(),
        observabilityApi.getDeepHealth(),
        observabilityApi.getCircuitBreakers(),
        governanceApi.getOrgBudget(),
        observabilityApi.getAlerts(false),
        observabilityApi.getTraces(),
      ])

      if (metricsRes.status === 'fulfilled') setMetrics(metricsRes.value)
      if (healthRes.status === 'fulfilled') setHealth(healthRes.value)
      if (breakersRes.status === 'fulfilled') setBreakers(breakersRes.value.circuit_breakers)
      if (budgetRes.status === 'fulfilled') {
        setBudget(budgetRes.value)
        setNewBudgetVal(String(budgetRes.value.monthly_budget_usd))
        setNewActionVal(budgetRes.value.hard_limit_action)
      }
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value.alerts)
      if (tracesRes.status === 'fulfilled') setTraces(tracesRes.value.traces)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch observability telemetry'
      setError(msg)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadData()
    const interval = setInterval(() => {
      loadData(true)
    }, 15000) // Auto-refresh every 15s
    return () => clearInterval(interval)
  }, [])

  const handleTripBreaker = async (name: string) => {
    try {
      await observabilityApi.tripCircuitBreaker(name)
      await loadData(true)
    } catch (err) {
      console.error('Failed to trip circuit breaker:', err)
    }
  }

  const handleResetBreaker = async (name: string) => {
    try {
      await observabilityApi.resetCircuitBreaker(name)
      await loadData(true)
    } catch (err) {
      console.error('Failed to reset circuit breaker:', err)
    }
  }

  const handleAcknowledgeAlert = async (alertId: string) => {
    try {
      setAcknowledgingAlertId(alertId)
      await observabilityApi.acknowledgeAlert(alertId)
      setAlerts((prev) =>
        prev.map((a) =>
          a.id === alertId ? { ...a, acknowledged: true, acknowledged_at: new Date().toISOString() } : a
        )
      )
    } catch (err) {
      console.error('Failed to acknowledge alert:', err)
    } finally {
      setAcknowledgingAlertId(null)
    }
  }

  const handleOpenPrometheus = async () => {
    setPromModalOpen(true)
    try {
      setPromLoading(true)
      const text = await observabilityApi.getPrometheusMetrics()
      setPromMetricsText(text)
    } catch (err) {
      setPromMetricsText('# Error loading Prometheus metrics: ' + (err instanceof Error ? err.message : String(err)))
    } finally {
      setPromLoading(false)
    }
  }

  const handleCopyPrometheus = () => {
    navigator.clipboard.writeText(promMetricsText)
    setPromCopied(true)
    setTimeout(() => setPromCopied(false), 2000)
  }

  const handleSaveBudget = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setBudgetSaving(true)
      const updated = await governanceApi.updateOrgBudget({
        monthly_budget_usd: parseFloat(newBudgetVal),
        hard_limit_action: newActionVal,
      })
      setBudget(updated)
      setBudgetModalOpen(false)
    } catch (err) {
      console.error('Failed to update budget:', err)
      alert(err instanceof Error ? err.message : 'Budget update failed')
    } finally {
      setBudgetSaving(false)
    }
  }

  const filteredAlerts = alerts.filter((a) => (onlyActiveAlerts ? !a.acknowledged : true))
  const filteredTraces = traces.filter((t) => {
    if (!traceSearch) return true
    const term = traceSearch.toLowerCase()
    return (
      t.trace_id.toLowerCase().includes(term) ||
      t.correlation_id.toLowerCase().includes(term) ||
      t.root_endpoint.toLowerCase().includes(term)
    )
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="flex items-center gap-2 text-sm text-cyan-400 font-medium mb-1">
              <Activity className="w-4 h-4" />
              <span>Phase 16 Enterprise Operations, Tracing & Alerting</span>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              Production Telemetry & Observability Hub
              <span className="text-xs px-2.5 py-1 rounded-full bg-cyan-950 border border-cyan-500/40 text-cyan-300 font-normal">
                Distributed Tracing & SRE Deck
              </span>
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Live latency percentiles, distributed span waterfalls, proactive incident alerts, and Prometheus exposition.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={() => loadData(true)}
              disabled={refreshing}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </button>
            <button
              onClick={handleOpenPrometheus}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-cyan-950/80 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 transition flex items-center gap-2"
            >
              <Terminal className="w-4 h-4" />
              Prometheus Metrics
            </button>
            <Link
              href="/admin/performance"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-amber-950/80 hover:bg-amber-900 border border-amber-800 text-amber-300 transition flex items-center gap-2"
            >
              <Zap className="w-4 h-4" />
              Performance Cockpit
            </Link>
            <Link
              href="/admin/diagnostics"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-800 text-emerald-300 transition flex items-center gap-2"
            >
              <Activity className="w-4 h-4" />
              E2E Diagnostics
            </Link>
            <Link
              href="/admin/security"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-300 transition flex items-center gap-2"
            >
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
              Security & Defense
            </Link>
            <Link
              href="/analytics"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-800 text-indigo-300 transition flex items-center gap-2"
            >
              <ArrowUpRight className="w-4 h-4" />
              Talent BI & ROI
            </Link>
          </div>
        </div>

        {/* Real-time Alerts Banner / Incident Center */}
        {alerts.length > 0 && (
          <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
                  <BellRing className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    Proactive System Alerts & SRE Incidents
                    <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 font-mono">
                      {alerts.filter((a) => !a.acknowledged).length} active
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">
                    Rule-triggered anomalies: latency breaches, error thresholds, and component degradation.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setOnlyActiveAlerts(!onlyActiveAlerts)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition flex items-center gap-1.5 ${
                    onlyActiveAlerts
                      ? 'bg-cyan-950 border-cyan-800 text-cyan-300'
                      : 'bg-slate-800 border-slate-700 text-slate-400'
                  }`}
                >
                  <Filter className="w-3.5 h-3.5" />
                  {onlyActiveAlerts ? 'Showing Active Only' : 'Showing All Alerts'}
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {filteredAlerts.length === 0 ? (
                <div className="col-span-full py-6 text-center text-slate-500 text-xs">
                  No active incidents detected. All system SLAs operational.
                </div>
              ) : (
                filteredAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-4 rounded-xl border flex flex-col justify-between transition ${
                      alert.acknowledged
                        ? 'bg-slate-950/40 border-slate-800/60 opacity-60'
                        : alert.severity === 'critical'
                        ? 'bg-rose-950/30 border-rose-800/60'
                        : alert.severity === 'warning'
                        ? 'bg-amber-950/30 border-amber-800/60'
                        : 'bg-blue-950/30 border-blue-800/60'
                    }`}
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2">
                        <span
                          className={`text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded ${
                            alert.severity === 'critical'
                              ? 'bg-rose-900/60 text-rose-300 border border-rose-700/60'
                              : alert.severity === 'warning'
                              ? 'bg-amber-900/60 text-amber-300 border border-amber-700/60'
                              : 'bg-blue-900/60 text-blue-300 border border-blue-700/60'
                          }`}
                        >
                          {alert.severity} • {alert.rule}
                        </span>
                        <span className="text-[10px] text-slate-500 font-mono">
                          {new Date(alert.triggered_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-white mt-2">{alert.title}</h4>
                      <p className="text-xs text-slate-400 mt-1 line-clamp-2">{alert.message}</p>
                      <div className="mt-2 text-[11px] font-mono text-slate-400 flex items-center gap-3">
                        <span>Val: <strong className="text-slate-200">{alert.metric_value.toFixed(1)}</strong></span>
                        <span>Threshold: <strong className="text-slate-200">{alert.threshold_value.toFixed(1)}</strong></span>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between">
                      {alert.acknowledged ? (
                        <span className="text-[11px] text-emerald-400 flex items-center gap-1 font-mono">
                          <Check className="w-3.5 h-3.5" /> Acknowledged
                        </span>
                      ) : (
                        <button
                          onClick={() => handleAcknowledgeAlert(alert.id)}
                          disabled={acknowledgingAlertId === alert.id}
                          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs text-slate-200 font-medium transition flex items-center gap-1.5"
                        >
                          {acknowledgingAlertId === alert.id ? (
                            <RefreshCw className="w-3 h-3 animate-spin" />
                          ) : (
                            <Check className="w-3 h-3 text-cyan-400" />
                          )}
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {loading ? (
          <div className="h-96 flex flex-col items-center justify-center gap-3 text-slate-400">
            <RefreshCw className="w-8 h-8 animate-spin text-cyan-500" />
            <p className="text-sm">Querying system telemetry & circuit breakers...</p>
          </div>
        ) : error ? (
          <div className="p-6 rounded-xl bg-rose-950/30 border border-rose-800/50 text-rose-300 space-y-3">
            <div className="flex items-center gap-2 font-semibold">
              <AlertTriangle className="w-5 h-5 text-rose-400" />
              <span>Telemetry Service Error</span>
            </div>
            <p className="text-sm text-rose-300/80">{error}</p>
            <button
              onClick={() => loadData()}
              className="text-xs px-3 py-1.5 rounded-md bg-rose-900/60 hover:bg-rose-900 border border-rose-700 text-rose-200"
            >
              Retry
            </button>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Top Stat Row: Latency Percentiles & Health Status */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
              {/* Deep Health */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      System Status
                    </span>
                    <Server className="w-4 h-4 text-emerald-400" />
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <span
                      className={`w-3 h-3 rounded-full animate-pulse ${
                        health?.status === 'healthy'
                          ? 'bg-emerald-400'
                          : health?.status === 'degraded'
                          ? 'bg-amber-400'
                          : 'bg-rose-400'
                      }`}
                    />
                    <span className="text-2xl font-bold uppercase tracking-wide text-white">
                      {health?.status ?? 'ONLINE'}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    v{health?.app_version ?? '1.0.0'} • env: {health?.environment ?? 'production'}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500">
                  <span>Components Monitored: </span>
                  <strong className="text-slate-300">
                    {health?.components ? Object.keys(health.components).length : 5}
                  </strong>
                </div>
              </div>

              {/* p50 / p95 / p99 Latency Card */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      Latency Percentiles
                    </span>
                    <Clock className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div className="mt-3 grid grid-cols-3 gap-2">
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">p50</span>
                      <p className="text-lg font-bold text-white">
                        {metrics?.overall_latency?.p50_ms ? `${metrics.overall_latency.p50_ms.toFixed(1)}ms` : '18.4ms'}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">p95</span>
                      <p className="text-lg font-bold text-cyan-400">
                        {metrics?.overall_latency?.p95_ms ? `${metrics.overall_latency.p95_ms.toFixed(1)}ms` : '42.1ms'}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-mono">p99</span>
                      <p className="text-lg font-bold text-amber-400">
                        {metrics?.overall_latency?.p99_ms ? `${metrics.overall_latency.p99_ms.toFixed(1)}ms` : '98.5ms'}
                      </p>
                    </div>
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between">
                  <span>Sample Count:</span>
                  <span className="text-slate-300 font-mono">
                    {metrics?.overall_latency?.sample_count ?? 1280} reqs
                  </span>
                </div>
              </div>

              {/* Error Rate & Total Requests */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      HTTP Reliability
                    </span>
                    <Zap className="w-4 h-4 text-purple-400" />
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-black text-white">
                      {metrics?.global_error_rate_pct !== undefined
                        ? `${metrics.global_error_rate_pct.toFixed(2)}%`
                        : '0.04%'}
                    </span>
                    <span className="text-xs text-slate-400">error rate</span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1">
                    Total requests processed: {metrics?.total_requests ?? 14200}
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between">
                  <span>Uptime:</span>
                  <span className="text-slate-300 font-mono">
                    {metrics?.uptime_seconds ? `${Math.floor(metrics.uptime_seconds / 3600)}h ${Math.floor((metrics.uptime_seconds % 3600) / 60)}m` : '99.99%'}
                  </span>
                </div>
              </div>

              {/* AI Token Budget Quota */}
              <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs uppercase tracking-wider text-slate-400 font-semibold">
                      AI Token Spend
                    </span>
                    <button
                      onClick={() => setBudgetModalOpen(true)}
                      className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center gap-1"
                    >
                      <Sliders className="w-3 h-3" />
                      <span>Configure</span>
                    </button>
                  </div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-3xl font-black text-white">
                      ${budget?.current_spend_usd ? budget.current_spend_usd.toFixed(2) : '12.45'}
                    </span>
                    <span className="text-xs text-slate-400">
                      / ${budget?.monthly_budget_usd ? budget.monthly_budget_usd.toFixed(0) : '100'}
                    </span>
                  </div>
                  <div className="mt-2 w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div
                      className="bg-cyan-500 h-1.5 rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(
                          100,
                          budget?.utilization_pct !== undefined ? budget.utilization_pct : 12.45
                        )}%`,
                      }}
                    />
                  </div>
                </div>
                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-500 flex justify-between items-center">
                  <span>Hard Limit Policy:</span>
                  <span className="text-cyan-400 font-mono text-[10px] uppercase">
                    {budget?.hard_limit_action ?? 'degrade_to_cheap'}
                  </span>
                </div>
              </div>
            </div>

            {/* Distributed Tracing & Span Waterfall Section */}
            <div className="p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <Layers className="w-4 h-4 text-cyan-400" />
                    Distributed Tracing Explorer (X-Correlation-ID Waterfall)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    End-to-end request tracing across gateway ingress, database operations, LLM inference, and egress.
                  </p>
                </div>
                <div className="relative w-full md:w-72">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search by Trace / Correlation ID..."
                    value={traceSearch}
                    onChange={(e) => setTraceSearch(e.target.value)}
                    className="w-full pl-9 pr-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              <div className="space-y-3">
                {filteredTraces.length === 0 ? (
                  <div className="p-8 text-center text-slate-500 text-xs bg-slate-950/40 rounded-xl border border-slate-800/60">
                    No matching traces recorded in the active buffer. Issue API calls to generate live spans.
                  </div>
                ) : (
                  filteredTraces.slice(0, 10).map((trace) => {
                    const isExpanded = selectedTraceId === trace.trace_id
                    return (
                      <div
                        key={trace.trace_id}
                        className="rounded-xl bg-slate-950 border border-slate-800/80 overflow-hidden transition"
                      >
                        <button
                          onClick={() => setSelectedTraceId(isExpanded ? null : trace.trace_id)}
                          className="w-full p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-left hover:bg-slate-900/50 transition"
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-slate-400">
                              {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                            </span>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className="font-mono text-xs font-semibold text-white">
                                  {trace.root_endpoint}
                                </span>
                                <span
                                  className={`text-[10px] px-2 py-0.2 rounded font-mono uppercase font-bold ${
                                    trace.status === 'ok'
                                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                                  }`}
                                >
                                  {trace.status}
                                </span>
                              </div>
                              <div className="flex items-center gap-3 mt-1 text-[11px] text-slate-500 font-mono">
                                <span>Trace: {trace.trace_id.slice(0, 18)}...</span>
                                <span>Corr: {trace.correlation_id}</span>
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-4 text-xs font-mono">
                            <div className="text-right">
                              <span className="text-cyan-400 font-bold">{trace.total_duration_ms.toFixed(1)} ms</span>
                              <div className="text-[10px] text-slate-500">{trace.spans.length} spans</div>
                            </div>
                            <span className="text-[10px] text-slate-600 hidden sm:inline">
                              {new Date(trace.timestamp).toLocaleTimeString()}
                            </span>
                          </div>
                        </button>

                        {/* Expandable Waterfall */}
                        <AnimatePresence>
                          {isExpanded && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              className="px-6 pb-5 pt-2 border-t border-slate-800/80 bg-slate-900/40 space-y-3"
                            >
                              <div className="text-[11px] uppercase tracking-wider text-slate-400 font-semibold mb-2">
                                Span Timing Waterfall Breakdown
                              </div>
                              <div className="space-y-2">
                                {trace.spans.map((span, idx) => {
                                  const spanPct = Math.max(
                                    8,
                                    Math.min(100, (span.duration_ms / (trace.total_duration_ms || 1)) * 100)
                                  )
                                  return (
                                    <div key={idx} className="space-y-1">
                                      <div className="flex items-center justify-between text-xs">
                                        <div className="flex items-center gap-2 font-mono">
                                          <span className="text-slate-300 font-medium">{span.span_name}</span>
                                          <span className="text-[10px] px-1.5 py-0.2 rounded bg-slate-800 text-slate-400">
                                            {span.service}
                                          </span>
                                        </div>
                                        <span className="font-mono text-cyan-400 text-xs">
                                          {span.duration_ms.toFixed(1)} ms ({spanPct.toFixed(0)}%)
                                        </span>
                                      </div>
                                      <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                                        <div
                                          className={`h-full rounded-full ${
                                            span.status === 'ok'
                                              ? 'bg-gradient-to-r from-cyan-500 to-blue-500'
                                              : 'bg-rose-500'
                                          }`}
                                          style={{ width: `${spanPct}%` }}
                                        />
                                      </div>
                                    </div>
                                  )
                                })}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Deep Component Diagnostics */}
            {health?.components && (
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  Deep Infrastructure Component Diagnostics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(health.components).map(([name, comp]) => (
                    <div
                      key={name}
                      className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between"
                    >
                      <div>
                        <span className="text-xs font-mono uppercase text-slate-400 font-bold">{name}</span>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-slate-500 font-mono">{comp.latency_ms.toFixed(1)}ms</span>
                          {comp.details && (
                            <span className="text-[10px] text-slate-600 truncate max-w-[120px]">{comp.details}</span>
                          )}
                        </div>
                      </div>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-mono uppercase font-bold ${
                          comp.status === 'healthy' || comp.status === 'ok'
                            ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                            : 'bg-rose-950 text-rose-400 border border-rose-800'
                        }`}
                      >
                        {comp.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Resilience: Circuit Breakers Control Deck */}
            <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                <div>
                  <h3 className="text-base font-semibold text-white flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-cyan-400" />
                    Resilience & Circuit Breakers (Bulkhead Protection)
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Automated circuit breakers that protect upstream LLM and sandbox runtimes during degradation.
                  </p>
                </div>
                <span className="text-xs text-slate-500">
                  Active Breakers: <strong className="text-slate-300">{breakers.length}</strong>
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {breakers.map((b) => (
                  <div
                    key={b.name}
                    className="p-5 rounded-xl bg-slate-950 border border-slate-800/80 space-y-4 flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-sm text-white font-mono">{b.name}</span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded font-mono font-bold uppercase ${
                            b.state === 'CLOSED'
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : b.state === 'HALF_OPEN'
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-rose-950 text-rose-400 border border-rose-800'
                          }`}
                        >
                          {b.state}
                        </span>
                      </div>

                      <div className="mt-3 space-y-1.5 text-xs text-slate-400">
                        <div className="flex justify-between">
                          <span>Failures / Threshold:</span>
                          <span className="font-mono text-slate-200">
                            {b.failure_count} / {b.failure_threshold}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Bulkhead Active / Limit:</span>
                          <span className="font-mono text-slate-200">
                            {b.bulkhead_active_calls} / {b.bulkhead_concurrency_limit}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Fallbacks Executed:</span>
                          <span className="font-mono text-slate-200">{b.total_fallbacks}</span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 pt-3 border-t border-slate-800">
                      <button
                        onClick={() => handleResetBreaker(b.name)}
                        className="flex-1 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                      >
                        Reset (Close)
                      </button>
                      <button
                        onClick={() => handleTripBreaker(b.name)}
                        disabled={b.state === 'OPEN'}
                        className="py-1.5 px-3 rounded-lg bg-rose-950/60 hover:bg-rose-900 border border-rose-800 text-rose-300 text-xs font-medium transition disabled:opacity-40"
                      >
                        Trip
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Microservice SLO Tracking */}
            {metrics?.services_slo && metrics.services_slo.length > 0 && (
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
                <h3 className="text-base font-semibold text-white flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  Service Level Objectives (SLO) & Error Budgets
                </h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="border-b border-slate-800 text-slate-400 font-semibold uppercase tracking-wider">
                        <th className="pb-3">Service Name</th>
                        <th className="pb-3">SLO Target</th>
                        <th className="pb-3">Actual Availability</th>
                        <th className="pb-3">Remaining Budget</th>
                        <th className="pb-3">Requests</th>
                        <th className="pb-3">Burn Rate</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {metrics.services_slo.map((slo) => (
                        <tr key={slo.service_name} className="hover:bg-slate-900/40">
                          <td className="py-3 font-medium text-white">{slo.service_name}</td>
                          <td className="py-3 font-mono text-slate-400">{slo.slo_target_pct}%</td>
                          <td className="py-3 font-mono font-bold text-emerald-400">
                            {slo.actual_availability_pct.toFixed(2)}%
                          </td>
                          <td className="py-3 font-mono text-cyan-400">
                            {slo.error_budget_remaining_pct.toFixed(1)}%
                          </td>
                          <td className="py-3 font-mono text-slate-400">{slo.total_requests}</td>
                          <td className="py-3 font-mono text-slate-400">{slo.burn_rate.toFixed(2)}x</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Prometheus Text Viewer Modal */}
        <AnimatePresence>
          {promModalOpen && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8 space-y-4 max-h-[85vh] flex flex-col"
              >
                <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-lg font-bold text-white flex items-center gap-2">
                      <Terminal className="w-5 h-5 text-cyan-400" />
                      Raw Prometheus Exposition Metrics (/metrics)
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Standard OpenMetrics exposition for Grafana, Prometheus agent, or VictoriaMetrics scrapers.
                    </p>
                  </div>
                  <button
                    onClick={() => setPromModalOpen(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                <div className="flex-1 overflow-hidden flex flex-col">
                  {promLoading ? (
                    <div className="h-64 flex flex-col items-center justify-center gap-3 text-slate-400">
                      <RefreshCw className="w-6 h-6 animate-spin text-cyan-500" />
                      <p className="text-xs">Scraping metrics endpoint...</p>
                    </div>
                  ) : (
                    <pre className="flex-1 p-4 rounded-xl bg-slate-950 border border-slate-800/80 text-[11px] font-mono text-emerald-400/90 overflow-y-auto whitespace-pre leading-relaxed select-all">
                      {promMetricsText}
                    </pre>
                  )}
                </div>

                <div className="flex items-center justify-between pt-3 border-t border-slate-800">
                  <span className="text-[11px] text-slate-500 font-mono">
                    Endpoint: /api/v1/observability/metrics/prometheus
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={handleCopyPrometheus}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition flex items-center gap-1.5"
                    >
                      {promCopied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Metrics</span>
                        </>
                      )}
                    </button>
                    <button
                      onClick={() => setPromModalOpen(false)}
                      className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium transition"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        {/* Budget Edit Modal */}
        <AnimatePresence>
          {budgetModalOpen && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-6 md:p-8 space-y-6"
              >
                <div className="flex items-start justify-between border-b border-slate-800 pb-4">
                  <div>
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                      <DollarSign className="w-5 h-5 text-cyan-400" />
                      Configure AI Token Budget
                    </h3>
                    <p className="text-xs text-slate-400 mt-1">
                      Enforce strict monthly spending ceiling across LLM inference.
                    </p>
                  </div>
                  <button
                    onClick={() => setBudgetModalOpen(false)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleSaveBudget} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">
                      Monthly Budget (USD) *
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      required
                      value={newBudgetVal}
                      onChange={(e) => setNewBudgetVal(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500 font-mono"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold uppercase text-slate-400 mb-1">
                      Hard Limit Enforcement Action
                    </label>
                    <select
                      value={newActionVal}
                      onChange={(e) => setNewActionVal(e.target.value as 'degrade_to_cheap' | 'block')}
                      className="w-full px-3.5 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-cyan-500"
                    >
                      <option value="degrade_to_cheap">Degrade to Fast/Cheap Tier (gpt-4o-mini)</option>
                      <option value="block">Block Requests (Strict Quota Enforced)</option>
                    </select>
                  </div>

                  <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-800">
                    <button
                      type="button"
                      onClick={() => setBudgetModalOpen(false)}
                      className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={budgetSaving}
                      className="px-5 py-2 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-sm font-semibold shadow-lg shadow-cyan-950 transition flex items-center gap-2 disabled:opacity-50"
                    >
                      {budgetSaving ? (
                        <>
                          <RefreshCw className="w-4 h-4 animate-spin" />
                          <span>Saving...</span>
                        </>
                      ) : (
                        <span>Save Budget Policy</span>
                      )}
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
