'use client'

import React, { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  Check,
  Zap,
  Sparkles,
  ShieldCheck,
  CreditCard,
  ChevronLeft,
  ArrowRight,
  Star,
  Layers,
  Cpu,
  GraduationCap,
  Building2,
  Lock,
} from 'lucide-react'
import PaymentModal from '@/components/payment/PaymentModal'
import { paymentApi, SubscriptionData } from '@/lib/api'
import { useAuthStore } from '@/store/auth'

export default function PricingPage() {
  const { user } = useAuthStore()
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly')
  const [selectedPlanForModal, setSelectedPlanForModal] = useState<string>('pro')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [currentSub, setCurrentSub] = useState<SubscriptionData | null>(null)
  const [upgradeSuccess, setUpgradeSuccess] = useState<string | null>(null)

  useEffect(() => {
    paymentApi
      .getSubscription()
      .then((sub) => setCurrentSub(sub))
      .catch(() => {})
  }, [])

  const handleOpenCheckout = (planId: string) => {
    setSelectedPlanForModal(planId)
    setIsModalOpen(true)
  }

  const handlePaymentSuccess = (sub: SubscriptionData) => {
    setCurrentSub(sub)
    setUpgradeSuccess(`Successfully upgraded to ${sub.tier} Plan! ${sub.credits_total} AI Credits are ready.`)
    setTimeout(() => setUpgradeSuccess(null), 6000)
  }

  const plans = [
    {
      id: 'starter',
      name: 'Starter Candidate',
      tagline: 'Ideal for college students preparing for campus placements and vivas.',
      priceMonthly: 29,
      priceYearly: 20,
      credits: '1,000 AI Credits',
      badge: 'Free Tier Available',
      features: [
        '10 Adaptive Mock Interviews',
        'Real-time Audio & WPM Delivery Analytics',
        'Core CS & DSA Curated Questions',
        'Detailed Bar Raiser Rubric Scorecards',
        'Standard Community Support',
      ],
      popular: false,
      btnText: (currentSub?.plan_id || currentSub?.tier?.toLowerCase()) === 'starter' ? 'Current Active Plan' : 'Select Starter',
    },
    {
      id: 'pro',
      name: 'Pro Engineer',
      tagline: 'Comprehensive prep for FAANG, Top Tier Product firms, and Unicorns.',
      priceMonthly: 79,
      priceYearly: 55,
      credits: '10,000 AI Credits',
      badge: 'Most Popular for CSE',
      features: [
        'Unlimited AI Mock Interviews & Practice Loops',
        '1536-Dimensional PGVector Semantic ATS Match',
        'AI Tutor Copilot: Live Hints & Deep Explanations',
        'Full Video & Audio Recording with Playback',
        'Custom System Design & Distributed Systems Scenarios',
        'Executive Recruiter Calibration & STAR Grading',
        'Priority GPU Inference & Instant Turnaround',
      ],
      popular: true,
      btnText: (currentSub?.plan_id || currentSub?.tier?.toLowerCase()) === 'pro' ? 'Current Active Plan' : 'Upgrade to Pro',
    },
    {
      id: 'business',
      name: 'Enterprise & Teams',
      tagline: 'For university placement cells, bootcamps, and enterprise recruiters.',
      priceMonthly: 199,
      priceYearly: 140,
      credits: '50,000 AI Credits',
      badge: 'Institutional & Recruiter',
      features: [
        '50,000 AI Credits per month',
        'Recruiter Portal with Bulk Candidate Comparison',
        'Custom ATS Taxonomy & Syllabus Import',
        'Multi-candidate Cohort Benchmarking & Twin AI',
        'GDPR/PII Data Retention Controls',
        'Dedicated 24/7 Enterprise Support Engineer',
      ],
      popular: false,
      btnText: (currentSub?.plan_id || currentSub?.tier?.toLowerCase()) === 'business' ? 'Current Active Plan' : 'Get Enterprise',
    },
  ]

  return (
    <div className="min-h-screen bg-[#070814] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200 py-12 px-4 sm:px-6 lg:px-8">
      {/* Volumetric background lights */}
      <div className="fixed top-0 left-1/4 w-[600px] h-[600px] bg-cyan-600/10 rounded-full blur-[150px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[150px] pointer-events-none" />

      <div className="max-w-6xl mx-auto space-y-10 relative z-10">
        {/* Top bar */}
        <div className="flex items-center justify-between pb-6 border-b border-white/[0.08]">
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.15] text-xs font-semibold text-slate-300 hover:text-white transition-all group"
          >
            <ChevronLeft className="w-4 h-4 text-slate-400 group-hover:-translate-x-0.5 transition-transform" />
            <span>Dashboard</span>
          </Link>

          <div className="flex items-center gap-3">
            {currentSub && (
              <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/30 text-xs font-mono text-cyan-300">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                <span>Tier: {currentSub.tier}</span>
                <span className="text-slate-400 font-sans">({currentSub.credits_remaining} credits left)</span>
              </span>
            )}
          </div>
        </div>

        {/* Success toast */}
        {upgradeSuccess && (
          <div className="p-4 rounded-2xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 text-sm flex items-center justify-between gap-3 animate-fade-in shadow-xl">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0" />
              <span className="font-semibold">{upgradeSuccess}</span>
            </div>
            <button
              onClick={() => setUpgradeSuccess(null)}
              className="text-emerald-400 hover:text-white text-xs font-mono cursor-pointer"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Heading */}
        <div className="text-center space-y-4 max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full text-xs font-mono font-medium bg-gradient-to-r from-cyan-500/15 via-indigo-500/15 to-purple-500/15 border border-cyan-500/30 text-cyan-300">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>Transparent SaaS Plans for Engineers &amp; Recruiters</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight">
            Accelerate Your Interview Mastery
          </h1>
          <p className="text-slate-400 text-base sm:text-lg leading-relaxed">
            Gain unlimited adaptive AI mock interviews, live AI Tutor pedagogical hints, video recording playback, and 1536-dimensional vector ATS match scoring.
          </p>

          {/* Billing Cycle Toggle */}
          <div className="pt-4 flex items-center justify-center">
            <div className="inline-flex items-center p-1 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-inner">
              <button
                type="button"
                onClick={() => setBillingCycle('monthly')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  billingCycle === 'monthly'
                    ? 'bg-cyan-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Monthly Billing
              </button>
              <button
                type="button"
                onClick={() => setBillingCycle('yearly')}
                className={`px-4 py-2 rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer ${
                  billingCycle === 'yearly'
                    ? 'bg-cyan-500 text-slate-950 shadow-md'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                <span>Yearly Billing</span>
                <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-emerald-400/20 text-emerald-300 font-mono font-black border border-emerald-400/30">
                  SAVE 30%
                </span>
              </button>
            </div>
          </div>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          {plans.map((p) => {
            const price = billingCycle === 'yearly' ? p.priceYearly : p.priceMonthly
            const isCurrent = (currentSub?.plan_id || currentSub?.tier?.toLowerCase()) === p.id

            return (
              <div
                key={p.id}
                className={`relative rounded-3xl p-7 flex flex-col justify-between transition-all duration-300 ${
                  p.popular
                    ? 'bg-gradient-to-b from-indigo-950/70 via-slate-900/90 to-slate-950/90 border-2 border-cyan-400 shadow-[0_0_40px_rgba(6,182,212,0.25)] ring-1 ring-cyan-400/50'
                    : 'bg-slate-900/50 border border-slate-800/80 hover:border-slate-700/80 hover:bg-slate-900/70'
                }`}
              >
                {p.popular && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full bg-gradient-to-r from-cyan-500 to-indigo-500 text-slate-950 text-[11px] font-black tracking-wider uppercase shadow-lg">
                    {p.badge}
                  </div>
                )}

                <div className="space-y-5">
                  <div className="space-y-1">
                    <div className="text-xs font-mono font-bold uppercase tracking-wider text-cyan-400">
                      {p.badge}
                    </div>
                    <h3 className="text-2xl font-extrabold text-white">{p.name}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed min-h-[36px]">{p.tagline}</p>
                  </div>

                  <div className="flex items-baseline gap-1 pt-2">
                    <span className="text-4xl font-black text-white font-mono">${price}</span>
                    <span className="text-xs text-slate-400 font-mono">/month</span>
                    {billingCycle === 'yearly' && (
                      <span className="text-[10px] text-slate-400 font-mono ml-2">billed annually</span>
                    )}
                  </div>

                  <div className="p-3 rounded-xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">AI Credits:</span>
                    <span className="font-bold text-cyan-300">{p.credits}</span>
                  </div>

                  <div className="space-y-3 pt-2">
                    <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-mono">
                      What is included:
                    </div>
                    <ul className="space-y-2.5">
                      {p.features.map((feat, i) => (
                        <li key={i} className="flex items-start gap-2.5 text-xs text-slate-300">
                          <Check className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
                          <span>{feat}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="pt-8">
                  <button
                    type="button"
                    onClick={() => handleOpenCheckout(p.id)}
                    disabled={isCurrent}
                    className={`w-full py-3.5 px-4 rounded-2xl text-xs font-extrabold tracking-wide uppercase transition-all duration-300 flex items-center justify-center gap-2 cursor-pointer shadow-lg ${
                      isCurrent
                        ? 'bg-slate-800 text-slate-400 border border-slate-700 cursor-not-allowed'
                        : p.popular
                        ? 'bg-gradient-to-r from-cyan-400 to-indigo-500 hover:from-cyan-300 hover:to-indigo-400 text-slate-950 hover:shadow-cyan-500/25'
                        : 'bg-white/[0.06] hover:bg-white/[0.12] text-white border border-white/[0.12]'
                    }`}
                  >
                    <span>{p.btnText}</span>
                    {!isCurrent && <ArrowRight className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            )
          })}
        </div>

        {/* Security / Enterprise Guarantee Note */}
        <div className="p-6 rounded-3xl bg-slate-900/40 border border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400 shrink-0">
              <Lock className="w-6 h-6" />
            </div>
            <div>
              <div className="text-sm font-bold text-white">Bank-Grade 256-Bit SSL &amp; PCI-DSS Level 1 Compliance</div>
              <div className="text-xs text-slate-400 mt-0.5">
                Processed with Stripe &amp; Razorpay payment gateways. 100% money-back guarantee within 7 days.
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] text-[11px] font-mono text-slate-300">
              Credit Cards • UPI • Netbanking
            </span>
          </div>
        </div>
      </div>

      {/* Payment Checkout Modal */}
      <PaymentModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        initialPlanId={selectedPlanForModal}
        billingCycle={billingCycle}
        onPaymentSuccess={handlePaymentSuccess}
      />
    </div>
  )
}
