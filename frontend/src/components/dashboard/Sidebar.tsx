'use client'

import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import {
  LayoutDashboard,
  Mic,
  FileText,
  Code2,
  Cpu,
  Building2,
  Coins,
  Sparkles,
  Briefcase,
  Flame,
  BarChart3,
  Network,
  Compass,
  Activity,
  Settings,
  ChevronLeft,
  ChevronRight,
  X,
} from 'lucide-react'

interface SidebarProps {
  isCollapsed: boolean
  onToggleCollapse: () => void
  onOpenUpgrade: () => void
  isMobileOpen?: boolean
  onCloseMobile?: () => void
}

export default function Sidebar({
  isCollapsed,
  onToggleCollapse,
  onOpenUpgrade,
  isMobileOpen = false,
  onCloseMobile,
}: SidebarProps) {
  const pathname = usePathname()

  const navGroups = [
    {
      group: 'Overview',
      items: [
        { name: 'Dashboard', icon: LayoutDashboard, href: '/dashboard' },
      ],
    },
    {
      group: 'Simulations',
      items: [
        { name: 'AI Mock Interview', icon: Mic, href: '/interview/new' },
        { name: 'Coding Round', icon: Code2, href: '/coding' },
        { name: 'System Design', icon: Cpu, href: '/system-design' },
        { name: 'Company Mode', icon: Building2, href: '/company-mode' },
        { name: 'Salary Negotiation', icon: Coins, href: '/negotiation' },
      ],
    },
    {
      group: 'Intelligence',
      items: [
        { name: 'ATS Analyzer', icon: FileText, href: '/ats' },
        { name: 'Career Intelligence', icon: Sparkles, href: '/resume-builder' },
        { name: 'Skill Graph', icon: Network, href: '/skills' },
        { name: 'Learning Roadmap', icon: Compass, href: '/learning' },
      ],
    },
    {
      group: 'Pipeline & Progress',
      items: [
        { name: 'Job Tracker', icon: Briefcase, href: '/job-tracker' },
        { name: 'Daily Challenge', icon: Flame, href: '/daily-challenge' },
        { name: 'Analytics & Ranking', icon: BarChart3, href: '/analytics' },
      ],
    },
    {
      group: 'Platform',
      items: [
        { name: 'Observability', icon: Activity, href: '/admin/observability' },
        { name: 'Diagnostics', icon: Settings, href: '/admin/diagnostics' },
      ],
    },
  ]

  const handleNavClick = () => {
    if (onCloseMobile) {
      onCloseMobile()
    }
  }

  const renderContent = (collapsed: boolean, isDrawer = false) => (
    <div className="flex flex-col h-full justify-between">
      {/* Top Header & Logo */}
      <div>
        <div className="h-16 px-4 flex items-center justify-between border-b border-white/[0.06] shrink-0">
          <Link
            href="/dashboard"
            onClick={handleNavClick}
            className="flex items-center gap-3 overflow-hidden"
          >
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-[0_0_20px_rgba(99,102,241,0.4)] shrink-0">
              <span className="text-white font-black text-base tracking-wider">AI</span>
            </div>
            {(!collapsed || isDrawer) && (
              <div className="truncate">
                <div className="font-extrabold text-sm tracking-wide text-white leading-tight">
                  INTERVIEW AI
                </div>
                <div className="text-[10px] font-mono text-cyan-400 leading-tight">
                  COMMAND CENTER
                </div>
              </div>
            )}
          </Link>

          {isDrawer ? (
            <button
              onClick={onCloseMobile}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors md:hidden"
              title="Close Navigation"
            >
              <X className="w-5 h-5" />
            </button>
          ) : (
            <button
              onClick={onToggleCollapse}
              title={collapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
              className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/[0.05] transition-colors"
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </button>
          )}
        </div>

        {/* Scrollable Navigation Groups */}
        <div className="p-3 space-y-5 overflow-y-auto max-h-[calc(100vh-160px)]">
          {navGroups.map((grp) => (
            <div key={grp.group} className="space-y-1">
              {(!collapsed || isDrawer) && (
                <div className="px-3 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-500 mb-1">
                  {grp.group}
                </div>
              )}
              {grp.items.map((item) => {
                const Icon = item.icon
                const isActive = pathname === item.href
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    onClick={handleNavClick}
                    title={collapsed && !isDrawer ? item.name : undefined}
                    className={`group relative flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-semibold transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-[0_4px_20px_rgba(99,102,241,0.35)]'
                        : 'text-slate-400 hover:text-white hover:bg-white/[0.04]'
                    } ${collapsed && !isDrawer ? 'justify-center px-0' : ''}`}
                  >
                    <Icon
                      className={`w-4 h-4 shrink-0 transition-transform group-hover:scale-110 ${
                        isActive ? 'text-white' : 'text-slate-400 group-hover:text-cyan-400'
                      }`}
                    />
                    {(!collapsed || isDrawer) && <span className="truncate">{item.name}</span>}

                    {collapsed && !isDrawer && (
                      <div className="absolute left-full ml-3 px-2.5 py-1.5 rounded-lg bg-[#0e122b] border border-white/10 text-white text-[11px] font-medium whitespace-nowrap shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto transition-opacity z-50">
                        {item.name}
                      </div>
                    )}
                  </Link>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Bottom Upgrade Card */}
      <div className="p-3 border-t border-white/[0.06] shrink-0">
        {collapsed && !isDrawer ? (
          <button
            onClick={() => {
              onOpenUpgrade()
              handleNavClick()
            }}
            title="Upgrade to Pro"
            className="w-10 h-10 mx-auto rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-lg hover:brightness-110 transition-all cursor-pointer"
          >
            <Sparkles className="w-5 h-5 animate-pulse" />
          </button>
        ) : (
          <div className="relative rounded-2xl p-3.5 bg-gradient-to-br from-[#121630] to-[#181a38] border border-indigo-500/25 text-center overflow-hidden">
            <div className="w-8 h-8 mx-auto rounded-xl bg-indigo-500/20 border border-indigo-400/30 flex items-center justify-center mb-2 shadow-[0_0_15px_rgba(99,102,241,0.25)]">
              <Sparkles className="w-4 h-4 text-indigo-400 animate-pulse" />
            </div>
            <h4 className="text-xs font-bold text-white mb-0.5">Upgrade to Pro</h4>
            <p className="text-[10px] text-slate-400 mb-2.5 leading-relaxed">
              Unlimited LangGraph loops &amp; 1536d vector scans.
            </p>
            <button
              onClick={() => {
                onOpenUpgrade()
                handleNavClick()
              }}
              className="block w-full py-1.5 px-3 rounded-lg bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-[11px] font-bold text-white shadow-md hover:brightness-110 transition-all cursor-pointer"
            >
              Upgrade Now
            </button>
          </div>
        )}
      </div>
    </div>
  )

  return (
    <>
      {/* 1. Mobile Off-Canvas Drawer Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 bg-black/75 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 bg-[#090b17] border-r border-white/[0.08] shadow-2xl transition-transform duration-300 md:hidden ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {renderContent(false, true)}
      </aside>

      {/* 2. Desktop Static Sidebar */}
      <aside
        className={`hidden md:flex md:flex-col h-screen shrink-0 bg-[#090b17] border-r border-white/[0.06] transition-all duration-300 select-none z-30 ${
          isCollapsed ? 'w-20' : 'w-64'
        }`}
      >
        {renderContent(isCollapsed, false)}
      </aside>
    </>
  )
}
