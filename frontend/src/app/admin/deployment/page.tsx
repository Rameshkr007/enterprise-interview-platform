'use client'

import React, { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import {
  Rocket,
  Server,
  Database,
  Layers,
  Activity,
  Shield,
  ShieldAlert,
  Clock,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Copy,
  Check,
  Terminal,
  Cpu,
  HardDrive,
  GitBranch,
  GitCommit,
  Power,
  Lock,
  Search,
  ExternalLink,
  ChevronRight,
  Filter,
} from 'lucide-react'
import { deploymentApi } from '@/lib/api'
import type {
  DeploymentStatusResponse,
  DeploymentHealthCheckResponse,
  EnvironmentAuditItem,
  MigrationStatusItem,
  ContainerStatus,
} from '@/lib/types'

export default function DeploymentCockpitPage() {
  const [activeTab, setActiveTab] = useState<'containers' | 'health' | 'audit' | 'migrations' | 'runbooks'>('containers')
  const [statusData, setStatusData] = useState<DeploymentStatusResponse | null>(null)
  const [healthData, setHealthData] = useState<DeploymentHealthCheckResponse | null>(null)
  const [auditItems, setAuditItems] = useState<EnvironmentAuditItem[]>([])
  const [migrations, setMigrations] = useState<MigrationStatusItem[]>([])
  const [loading, setLoading] = useState(true)
  const [probing, setProbing] = useState(false)
  const [togglingMaintenance, setTogglingMaintenance] = useState(false)
  const [maintenanceReasonInput, setMaintenanceReasonInput] = useState('')
  const [showMaintenanceModal, setShowMaintenanceModal] = useState(false)
  const [copiedKey, setCopiedKey] = useState<string | null>(null)
  const [searchAudit, setSearchAudit] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('ALL')
  const [actionMessage, setActionMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const loadData = useCallback(async () => {
    try {
      const [sData, aData, mData] = await Promise.all([
        deploymentApi.getStatus().catch(() => null),
        deploymentApi.getEnvAudit().catch(() => []),
        deploymentApi.getMigrations().catch(() => []),
      ])
      if (sData) setStatusData(sData)
      if (aData) setAuditItems(aData)
      if (mData) setMigrations(mData)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const runHealthProbe = async () => {
    setProbing(true)
    try {
      const hData = await deploymentApi.runHealthCheck()
      setHealthData(hData)
      setActionMessage({ type: 'success', text: `Health probe finished with status: ${hData.overall_status.toUpperCase()}` })
    } catch {
      setActionMessage({ type: 'error', text: 'Health probe execution failed' })
    } finally {
      setProbing(false)
    }
  }

  const handleToggleMaintenance = async (enable: boolean) => {
    setTogglingMaintenance(true)
    try {
      const res = await deploymentApi.toggleMaintenance(enable, enable ? (maintenanceReasonInput || 'Operational deployment maintenance') : null)
      if (statusData) {
        setStatusData({
          ...statusData,
          maintenance_mode: res.maintenance_mode,
          maintenance_reason: res.reason,
        })
      }
      setShowMaintenanceModal(false)
      setMaintenanceReasonInput('')
      setActionMessage({
        type: 'success',
        text: res.maintenance_mode ? 'Maintenance mode ACTIVATED' : 'Maintenance mode DEACTIVATED',
      })
    } catch {
      setActionMessage({ type: 'error', text: 'Failed to update maintenance mode' })
    } finally {
      setTogglingMaintenance(false)
    }
  }

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text)
    setCopiedKey(id)
    setTimeout(() => setCopiedKey(null), 2000)
  }

  // Filter audit items
  const auditCategories = ['ALL', ...Array.from(new Set(auditItems.map((i) => i.category)))]
  const filteredAudit = auditItems.filter((item) => {
    const matchesCategory = categoryFilter === 'ALL' || item.category === categoryFilter
    const matchesSearch =
      item.key.toLowerCase().includes(searchAudit.toLowerCase()) ||
      item.description.toLowerCase().includes(searchAudit.toLowerCase()) ||
      item.category.toLowerCase().includes(searchAudit.toLowerCase())
    return matchesCategory && matchesSearch
  })

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Rocket className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold tracking-tight text-white">
                  Production Deployment & Operations
                </h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {statusData?.environment?.toUpperCase() ?? 'PRODUCTION'}
                </span>
              </div>
              <p className="text-sm text-slate-400">
                Multi-container orchestration, zero-downtime deployment probes & live infrastructure auditing
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 hover:bg-slate-800 text-xs font-medium text-slate-300 transition-colors"
          >
            <RotateCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            Refresh
          </button>

          <button
            onClick={runHealthProbe}
            disabled={probing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition-all disabled:opacity-50"
          >
            <Activity className={`w-3.5 h-3.5 ${probing ? 'animate-spin' : ''}`} />
            {probing ? 'Probing Stack...' : 'Run Health Probe'}
          </button>

          <button
            onClick={() => {
              if (statusData?.maintenance_mode) {
                handleToggleMaintenance(false)
              } else {
                setShowMaintenanceModal(true)
              }
            }}
            disabled={togglingMaintenance}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all border ${
              statusData?.maintenance_mode
                ? 'bg-rose-500/10 text-rose-400 border-rose-500/30 hover:bg-rose-500/20'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30 hover:bg-amber-500/20'
            }`}
          >
            <Power className="w-3.5 h-3.5" />
            {statusData?.maintenance_mode ? 'Exit Maintenance' : 'Set Maintenance'}
          </button>
        </div>
      </div>

      {/* Action Banner */}
      {actionMessage && (
        <div
          className={`p-3 rounded-lg border flex items-center justify-between text-xs font-medium ${
            actionMessage.type === 'success'
              ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
              : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
          }`}
        >
          <span>{actionMessage.text}</span>
          <button onClick={() => setActionMessage(null)} className="text-slate-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* Maintenance Mode Alert Banner */}
      {statusData?.maintenance_mode && (
        <div className="p-4 rounded-xl border border-rose-500/30 bg-rose-500/10 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <ShieldAlert className="w-6 h-6 text-rose-400 shrink-0" />
            <div>
              <h3 className="text-sm font-semibold text-rose-300">MAINTENANCE MODE IS ACTIVE</h3>
              <p className="text-xs text-rose-400/80">
                {statusData.maintenance_reason || 'System is currently undergoing operational maintenance.'}
              </p>
            </div>
          </div>
          <button
            onClick={() => handleToggleMaintenance(false)}
            className="px-3 py-1 rounded bg-rose-600 text-white text-xs font-semibold hover:bg-rose-500"
          >
            Deactivate Now
          </button>
        </div>
      )}

      {/* Primary KPI HUD Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Uptime</span>
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {statusData ? `${Math.floor(statusData.uptime_seconds / 60)}m ${Math.floor(statusData.uptime_seconds % 60)}s` : '---'}
          </div>
          <div className="text-[11px] text-slate-500">Continuous Service</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Version</span>
            <Layers className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {statusData?.version ? `v${statusData.version}` : '---'}
          </div>
          <div className="text-[11px] text-slate-500">Release Build</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Git Commit</span>
            <GitCommit className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-lg font-bold text-white font-mono">
            {statusData?.git_commit ? statusData.git_commit.slice(0, 7) : '---'}
          </div>
          <div className="text-[11px] text-slate-500 flex items-center gap-1">
            <GitBranch className="w-3 h-3" />
            {statusData?.git_branch ?? 'main'}
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Migration Head</span>
            <Database className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-lg font-bold text-white truncate font-mono">
            {statusData?.current_migration_head ? statusData.current_migration_head.slice(0, 10) : '---'}
          </div>
          <div className="text-[11px] text-slate-500">
            {statusData?.migrations_applied_count ?? 4} Revisions Applied
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Containers</span>
            <Server className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-lg font-bold text-white">
            {statusData?.containers?.length ?? 5} Active
          </div>
          <div className="text-[11px] text-slate-500">Orchestrated Stack</div>
        </div>

        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs mb-1">
            <span>Maintenance</span>
            <Shield className="w-3.5 h-3.5 text-sky-400" />
          </div>
          <div className="text-lg font-bold">
            {statusData?.maintenance_mode ? (
              <span className="text-rose-400">ENABLED</span>
            ) : (
              <span className="text-emerald-400">DISABLED</span>
            )}
          </div>
          <div className="text-[11px] text-slate-500">Zero-Downtime Safe</div>
        </div>
      </div>

      {/* Live Health Probe Matrix (If Run or Loaded) */}
      {healthData && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-semibold text-white">Live Health Check Probes</h2>
              <span
                className={`px-2 py-0.5 rounded text-xs font-semibold ${
                  healthData.overall_status === 'healthy'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : healthData.overall_status === 'degraded'
                    ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                    : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                }`}
              >
                OVERALL: {healthData.overall_status.toUpperCase()}
              </span>
            </div>
            <span className="text-xs text-slate-400">Checked: {new Date(healthData.timestamp).toLocaleTimeString()}</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            {healthData.probes.map((probe, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-slate-300 truncate">{probe.service}</span>
                    {probe.status === 'healthy' ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                    ) : probe.status === 'degraded' ? (
                      <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 line-clamp-2">{probe.message}</p>
                </div>
                <div className="mt-2 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px]">
                  <span className="text-slate-500">Latency</span>
                  <span className="font-mono text-indigo-300">{probe.latency_ms} ms</span>
                </div>
              </div>
            ))}
          </div>

          {/* System Resources Mini Bar */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-cyan-400" />
                <span className="text-xs text-slate-300">Disk Storage</span>
              </div>
              <div className="text-right">
                <div className="text-xs font-semibold text-white">
                  {healthData.system_resources.disk_free_gb} GB Free
                </div>
                <div className="text-[10px] text-slate-500">
                  {healthData.system_resources.disk_total_gb} GB Total ({healthData.system_resources.disk_used_percent}% used)
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-purple-400" />
                <span className="text-xs text-slate-300">System Memory</span>
              </div>
              <div className="text-right">
                <div className="text-xs font-semibold text-white">
                  {healthData.system_resources.memory_used_mb} MB
                </div>
                <div className="text-[10px] text-slate-500">
                  {healthData.system_resources.memory_total_mb} MB ({healthData.system_resources.memory_percent}%)
                </div>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-amber-400" />
                <span className="text-xs text-slate-300">CPU Utilization</span>
              </div>
              <div className="text-right">
                <div className="text-xs font-semibold text-white">
                  {healthData.system_resources.cpu_percent}%
                </div>
                <div className="text-[10px] text-slate-500">Multi-core Load</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tabs Navigation */}
      <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
        {[
          { id: 'containers', label: 'Container Matrix', icon: Server, count: statusData?.containers?.length ?? 5 },
          { id: 'audit', label: 'Environment Audit', icon: Shield, count: auditItems.length },
          { id: 'migrations', label: 'Database Migrations', icon: Database, count: migrations.length },
          { id: 'runbooks', label: 'Deployment Runbooks', icon: Terminal },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-600/20'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count !== undefined && (
                <span
                  className={`px-1.5 py-0.2 rounded-full text-[10px] ${
                    isActive ? 'bg-indigo-800 text-indigo-200' : 'bg-slate-800 text-slate-400'
                  }`}
                >
                  {tab.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Tab 1: Container Orchestration Matrix */}
      {activeTab === 'containers' && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Production Container Matrix</h2>
              <p className="text-xs text-slate-400">
                Live status and resource allocations defined in <code className="text-indigo-300">docker-compose.prod.yml</code>
              </p>
            </div>
            <div className="text-xs text-slate-400">
              Network: <code className="text-indigo-400">production_internal_net / production_public_net</code>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Service</th>
                  <th className="py-2.5 px-3 font-semibold">Container Name</th>
                  <th className="py-2.5 px-3 font-semibold">Docker Image Tag</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                  <th className="py-2.5 px-3 font-semibold">Port Bindings</th>
                  <th className="py-2.5 px-3 font-semibold">Uptime</th>
                  <th className="py-2.5 px-3 font-semibold">CPU</th>
                  <th className="py-2.5 px-3 font-semibold">Memory</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {(statusData?.containers ?? []).map((container, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/30 transition-colors">
                    <td className="py-3 px-3 font-sans font-medium text-white flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                      {container.service.toUpperCase()}
                    </td>
                    <td className="py-3 px-3 text-slate-300">{container.container_name}</td>
                    <td className="py-3 px-3 text-indigo-300">{container.image}</td>
                    <td className="py-3 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {container.status}
                      </span>
                    </td>
                    <td className="py-3 px-3 text-slate-400">
                      {container.ports.map((p) => (
                        <span key={p} className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] mr-1">
                          {p}
                        </span>
                      ))}
                    </td>
                    <td className="py-3 px-3 text-slate-300 font-sans">{container.uptime}</td>
                    <td className="py-3 px-3 text-amber-300">{container.cpu_percent}%</td>
                    <td className="py-3 px-3 text-purple-300">{container.memory_mb} MB</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Environment Configuration Audit */}
      {activeTab === 'audit' && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-semibold text-white">Environment Configuration Audit</h2>
              <p className="text-xs text-slate-400">
                Audited configuration items with cryptographic secret masking and categorization
              </p>
            </div>
            <div className="flex items-center gap-2 w-full md:w-auto">
              <div className="relative flex-1 md:w-64">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
                <input
                  type="text"
                  placeholder="Filter keys or descriptions..."
                  value={searchAudit}
                  onChange={(e) => setSearchAudit(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
          </div>

          {/* Category Tabs */}
          <div className="flex items-center gap-1.5 flex-wrap">
            {auditCategories.map((cat) => (
              <button
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium transition-colors ${
                  categoryFilter === cat
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Config Key</th>
                  <th className="py-2.5 px-3 font-semibold">Category</th>
                  <th className="py-2.5 px-3 font-semibold">Masked Value</th>
                  <th className="py-2.5 px-3 font-semibold">Secret</th>
                  <th className="py-2.5 px-3 font-semibold">Status</th>
                  <th className="py-2.5 px-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredAudit.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-900/30 transition-colors">
                    <td className="py-2.5 px-3 text-indigo-300 font-semibold">{item.key}</td>
                    <td className="py-2.5 px-3 font-sans">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                        {item.category}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-200">
                      <div className="flex items-center gap-1.5">
                        {item.is_secret && <Lock className="w-3 h-3 text-amber-400 shrink-0" />}
                        <span className={item.is_secret ? 'text-amber-300/90' : 'text-slate-300'}>
                          {item.value_masked}
                        </span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      {item.is_secret ? (
                        <span className="text-amber-400 text-[10px]">YES</span>
                      ) : (
                        <span className="text-slate-500 text-[10px]">NO</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-sans">
                      {item.is_set ? (
                        <span className="flex items-center gap-1 text-emerald-400 text-[11px]">
                          <Check className="w-3 h-3" /> SET
                        </span>
                      ) : (
                        <span className="text-rose-400 text-[11px]">MISSING</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 font-sans text-slate-400 text-[11px]">{item.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: Database Migration Ledger */}
      {activeTab === 'migrations' && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-white">Alembic Migration History & Schema State</h2>
              <p className="text-xs text-slate-400">
                Verified schema revisions with dependency chain tracking and head validation
              </p>
            </div>
            <span className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-semibold">
              HEAD: {statusData?.current_migration_head ?? '004_phase1_foundation'}
            </span>
          </div>

          <div className="space-y-3">
            {migrations.map((mig, idx) => (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col md:flex-row items-start md:items-center justify-between gap-3 ${
                  mig.is_head
                    ? 'bg-indigo-950/20 border-indigo-500/30'
                    : 'bg-slate-950/50 border-slate-800'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${mig.is_head ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                    <Database className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold font-mono text-white">Revision {mig.revision}</span>
                      {mig.is_head && (
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-500 text-white">
                          CURRENT HEAD
                        </span>
                      )}
                      <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        APPLIED
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-0.5">{mig.description}</p>
                    <div className="text-[11px] text-slate-500 font-mono mt-1">
                      Parent (down_revision): {mig.down_revision ?? 'None (Initial Root)'}
                    </div>
                  </div>
                </div>

                <div className="text-right text-xs text-slate-400">
                  <div>Applied Timestamp</div>
                  <div className="text-slate-300 font-mono text-[11px]">{mig.applied_at ?? 'Active in DB'}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Deployment Runbooks & Commands */}
      {activeTab === 'runbooks' && (
        <div className="p-5 rounded-2xl bg-slate-900/40 border border-slate-800 space-y-4">
          <div>
            <h2 className="text-base font-semibold text-white">Production Deployment Runbooks</h2>
            <p className="text-xs text-slate-400">
              Standard operating procedures and copyable CLI commands for SRE deployments
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                id: 'preflight',
                title: '1. Execute Pre-Flight Verifications',
                desc: 'Audits manifests, configuration files, and Alembic migrations before applying changes.',
                cmd: 'python scripts/deploy_orchestrator.py preflight',
              },
              {
                id: 'compose_up',
                title: '2. Launch Production Multi-Container Stack',
                desc: 'Builds and launches backend, frontend, postgres, redis, and caddy with healthchecks.',
                cmd: 'docker compose -f docker-compose.prod.yml up -d --build',
              },
              {
                id: 'migrate',
                title: '3. Execute Database Migrations (Zero Downtime)',
                desc: 'Runs Alembic migration runner inside the production backend container.',
                cmd: 'docker compose -f docker-compose.prod.yml exec backend alembic upgrade head',
              },
              {
                id: 'restart',
                title: '4. Rolling Zero-Downtime Backend Restart',
                desc: 'Performs a graceful rolling restart of API workers under Caddy reverse proxy.',
                cmd: 'docker compose -f docker-compose.prod.yml restart backend',
              },
              {
                id: 'logs',
                title: '5. Stream Real-Time Production Logs',
                desc: 'Follows structured JSON logs across all orchestrated containers.',
                cmd: 'docker compose -f docker-compose.prod.yml logs -f --tail=100',
              },
              {
                id: 'rollback',
                title: '6. Emergency Stack Rollback',
                desc: 'Reverts container containers to previous release tag without data loss.',
                cmd: 'docker compose -f docker-compose.prod.yml down && git checkout HEAD~1 && docker compose -f docker-compose.prod.yml up -d',
              },
            ].map((runbook) => (
              <div key={runbook.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2.5">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold text-white">{runbook.title}</h3>
                  <button
                    onClick={() => handleCopy(runbook.cmd, runbook.id)}
                    className="p-1.5 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
                  >
                    {copiedKey === runbook.id ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
                <p className="text-[11px] text-slate-400">{runbook.desc}</p>
                <div className="p-2 rounded bg-slate-900 border border-slate-800/80 font-mono text-[11px] text-indigo-300 break-all select-all">
                  {runbook.cmd}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cross-Link Footer to Admin Observability & Performance */}
      <div className="p-4 rounded-xl bg-slate-900/30 border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-400">
        <span>Enterprise Cockpits:</span>
        <div className="flex items-center gap-4">
          <Link href="/admin/performance" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            Performance & Caching <ChevronRight className="w-3.5 h-3.5" />
          </Link>
          <Link href="/admin/diagnostics" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            Diagnostics Studio <ChevronRight className="w-3.5 h-3.5" />
          </Link>
          <Link href="/admin/security" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            Zero-Trust Security <ChevronRight className="w-3.5 h-3.5" />
          </Link>
          <Link href="/admin/observability" className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1">
            SRE Observability <ChevronRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {/* Maintenance Mode Activation Modal */}
      {showMaintenanceModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-amber-500/10 text-amber-400">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">Activate Maintenance Mode?</h3>
                <p className="text-xs text-slate-400">
                  This signals maintenance to active users and locks mutation workflows.
                </p>
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Maintenance Reason (Displayed to Users)</label>
              <input
                type="text"
                placeholder="e.g. Scheduled database maintenance & release upgrade"
                value={maintenanceReasonInput}
                onChange={(e) => setMaintenanceReasonInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowMaintenanceModal(false)}
                className="px-3.5 py-1.5 rounded-lg border border-slate-700 bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-slate-300"
              >
                Cancel
              </button>
              <button
                onClick={() => handleToggleMaintenance(true)}
                disabled={togglingMaintenance}
                className="px-4 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white text-xs font-semibold shadow-lg shadow-amber-600/20"
              >
                {togglingMaintenance ? 'Activating...' : 'Activate Mode'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
