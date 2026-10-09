'use client'

import React, { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthStore } from '@/store/auth'
import { paymentApi } from '@/lib/api'
import Sidebar from '@/components/dashboard/Sidebar'
import Topbar from '@/components/dashboard/Topbar'
import CommandPalette from '@/components/dashboard/CommandPalette'
import WelcomeHeader from '@/components/dashboard/WelcomeHeader'
import MetricCards from '@/components/dashboard/MetricCards'
import FeatureCards from '@/components/dashboard/FeatureCards'
import AIIntelligencePanel from '@/components/dashboard/AIIntelligencePanel'
import SkillHeatmap from '@/components/dashboard/SkillHeatmap'
import ActivityTimeline from '@/components/dashboard/ActivityTimeline'
import JobPipelineWidget from '@/components/dashboard/JobPipelineWidget'
import DailyChallengeWidget from '@/components/dashboard/DailyChallengeWidget'
import LearningRoadmapWidget from '@/components/dashboard/LearningRoadmapWidget'
import PricingPlansSection from '@/components/dashboard/PricingPlansSection'
import PaymentModal from '@/components/payment/PaymentModal'
import { ShieldCheck, Sparkles, Terminal } from 'lucide-react'

export default function DashboardPage() {
  const { user, fetchMe, logout } = useAuthStore()
  const router = useRouter()

  // Layout & Navigation State
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false)

  // Subscription & Tier State
  const [currentTier, setCurrentTier] = useState<string>('Pro Candidate')
  const [creditsRemaining, setCreditsRemaining] = useState<number>(10000)

  // Checkout Modal State
  const [isPaymentModalOpen, setIsPaymentModalOpen] = useState(false)
  const [selectedPlanForPayment, setSelectedPlanForPayment] = useState<string>('pro')

  useEffect(() => {
    fetchMe().then(() => {
      if (!useAuthStore.getState().user) {
        router.push('/login')
      } else {
        // Fetch active subscription from PostgreSQL database
        paymentApi
          .getSubscription()
          .then((sub) => {
            if (sub) {
              setCurrentTier(`${sub.tier.charAt(0).toUpperCase() + sub.tier.slice(1)} Candidate`)
              setCreditsRemaining(sub.credits_remaining)
            }
          })
          .catch(() => {})

        // Check for return from Stripe checkout
        if (typeof window !== 'undefined') {
          const params = new URLSearchParams(window.location.search)
          const paymentStatus = params.get('payment')
          const sessionId = params.get('session_id')
          if (paymentStatus === 'success' && sessionId) {
            paymentApi
              .verifyPayment({ session_id: sessionId })
              .then((res) => {
                setCurrentTier(`${res.subscription.tier.charAt(0).toUpperCase() + res.subscription.tier.slice(1)} Candidate`)
                setCreditsRemaining(res.subscription.credits_remaining)
              })
              .catch(() => {})
          }
        }
      }
    })
  }, [fetchMe, router])

  // Global Keyboard Shortcut: Command / Ctrl + K opens Command Palette
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        setIsCommandPaletteOpen((prev) => !prev)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  const handleOpenUpgrade = (planId: string = 'pro') => {
    setSelectedPlanForPayment(planId)
    setIsPaymentModalOpen(true)
  }

  const handlePaymentSuccess = (subData: any) => {
    setCurrentTier(`${subData.tier.charAt(0).toUpperCase() + subData.tier.slice(1)} Candidate`)
    setCreditsRemaining(subData.credits_remaining)
  }

  return (
    <div className="flex h-screen w-full bg-[#070814] text-slate-100 overflow-hidden selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* 1. Collapsible Sidebar Navigation (Desktop Fixed + Mobile Off-Canvas Drawer) */}
      <Sidebar
        isCollapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        onOpenUpgrade={() => handleOpenUpgrade('pro')}
        isMobileOpen={isMobileMenuOpen}
        onCloseMobile={() => setIsMobileMenuOpen(false)}
      />

      {/* 2. Main Viewport & Scroll Container: strictly handles single smooth vertical scroll */}
      <div className="flex-1 h-screen flex flex-col min-w-0 overflow-y-auto overflow-x-hidden">
        {/* Top Navigation Bar */}
        <Topbar
          userName={user?.full_name || 'Candidate'}
          userEmail={user?.email || 'candidate@enterprise.ai'}
          tier={currentTier}
          credits={creditsRemaining}
          onOpenCommandPalette={() => setIsCommandPaletteOpen(true)}
          onOpenUpgrade={() => handleOpenUpgrade('pro')}
          onLogout={logout}
          onOpenMobileMenu={() => setIsMobileMenuOpen(true)}
        />

        {/* Dashboard Main Scrollable Body */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 space-y-8 max-w-7xl mx-auto w-full overflow-x-hidden">
          {/* Section A: Welcome & Career Overview with 3D Holographic Brain */}
          <WelcomeHeader
            userName={user?.full_name || 'Senior Engineer'}
            targetRole="Staff Systems Architect & Tech Lead"
            readinessScore={88.4}
            latestSessionId={null}
          />

          {/* Section B: 6 Core Performance Metrics */}
          <MetricCards
            latestScore={92.4}
            avgScore={88.6}
            totalSessions={14}
            totalAtsScans={28}
            skillProgress={84.5}
            streakDays={14}
          />

          {/* Section C: 9 Career Acceleration Feature Modules */}
          <FeatureCards />

          {/* Section D: AI Intelligence Panel (Skill Gaps + Live GPT-4o Copilot) */}
          <AIIntelligencePanel />

          {/* Section E: Skill Competency Heatmap & Trajectory Chart */}
          <SkillHeatmap />

          {/* Section F: Pipeline & Daily Challenge Grids */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-6">
              <JobPipelineWidget />
            </div>
            <div className="lg:col-span-6 space-y-6">
              <DailyChallengeWidget />
              <LearningRoadmapWidget />
            </div>
          </div>

          {/* Section G: Interview Activity Timeline (Real Session DB Log) */}
          <ActivityTimeline />

          {/* Section H: Production Pricing & Subscription Tiers */}
          <PricingPlansSection
            currentTier={currentTier}
            onOpenPaymentModal={handleOpenUpgrade}
          />

          {/* Enterprise Footer */}
          <footer className="pt-8 pb-12 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <span>Enterprise AI Career Intelligence Engine v2.4.0 &bull; 256-bit AES Encrypted</span>
            </div>
            <div className="flex items-center gap-4">
              <span>LangGraph Multi-Agent State Machine</span>
              <span>&bull;</span>
              <span>PGVector Embeddings</span>
              <span>&bull;</span>
              <span>Stripe + UPI Gateway</span>
            </div>
          </footer>
        </main>
      </div>

      {/* 3. Global Command Palette Modal (⌘K) */}
      <CommandPalette
        isOpen={isCommandPaletteOpen}
        onClose={() => setIsCommandPaletteOpen(false)}
      />

      {/* 4. Complete Production Payment Modal */}
      <PaymentModal
        isOpen={isPaymentModalOpen}
        onClose={() => setIsPaymentModalOpen(false)}
        initialPlanId={selectedPlanForPayment}
        billingCycle="yearly"
        onPaymentSuccess={handlePaymentSuccess}
      />
    </div>
  )
}
