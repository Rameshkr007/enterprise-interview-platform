'use client'

import React, { useState } from 'react'
import { Check, Zap, Sparkles, ShieldCheck, Building2, ArrowRight } from 'lucide-react'

interface PricingPlansSectionProps {
  currentTier: string
  onOpenPaymentModal: (planId: string) => void
}

export default function PricingPlansSection({
  currentTier,
  onOpenPaymentModal,
}: PricingPlansSectionProps) {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'yearly'>('yearly')

  const plans = [
    {
      id: 'free',
      name: 'Starter Candidate',
      price: '$0',
      period: 'forever',
      description: 'Essential practice for engineering students and junior developers.',
      features: [
        '3 Adaptive AI Mock Interviews / month',
        '5 ATS Semantic Resume Scans',
        'Standard Algorithm Sandbox',
        'Basic Performance Diagnostic Report',
        'Community Discord Support',
      ],
      cta: 'Current Plan',
      isCurrent: currentTier.toLowerCase().includes('free') || currentTier.toLowerCase().includes('starter'),
      isPopular: false,
    },
    {
      id: 'pro',
      name: 'Pro Candidate',
      price: billingCycle === 'yearly' ? '$29' : '$39',
      period: 'per month',
      badge: 'Most Popular',
      description: 'Full simulation suite designed to clear Tier-1 & FAANG technical loops.',
      features: [
        'Unlimited Adaptive Mock Interviews',
        '10,000 AI Credits allocated monthly',
        'FAANG Company Rubric Simulations (Google, Meta, Amazon)',
        'Live Audio Tone, Pace & Speech Jitter Analytics',
        'Executive Behavioral STAR Scoring',
        'Salary Negotiation Counter-Offer Coach',
        'Real-time PGVector Semantic ATS Matcher',
      ],
      cta: 'Upgrade to Pro',
      isCurrent: currentTier.toLowerCase().includes('pro'),
      isPopular: true,
    },
    {
      id: 'enterprise',
      name: 'Enterprise / Career Suite',
      price: billingCycle === 'yearly' ? '$89' : '$99',
      period: 'per month',
      description: 'Dedicated mentorship, unlimited credits, and 1-on-1 human debriefs.',
      features: [
        'Everything in Pro Candidate',
        'Unlimited AI Inference & Speech Credits',
        'Custom System Design Arch Canvas with Live Verification',
        'Staff & Principal Level Architecture Question Bank',
        'Private AI Resume Tailoring per Target Requisition',
        'Priority 24/7 SLA & Dedicated Career Coach',
      ],
      cta: 'Upgrade to Enterprise',
      isCurrent: currentTier.toLowerCase().includes('enterprise'),
      isPopular: false,
    },
  ]

  return (
    <div className="rounded-2xl border border-slate-800/80 bg-gradient-to-b from-slate-900/90 to-slate-950/90 p-8 backdrop-blur-xl shadow-lg shadow-black/40">
      <div className="text-center max-w-xl mx-auto mb-8">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-bold mb-3">
          <Zap className="w-3.5 h-3.5" />
          Production Career Subscriptions
        </div>
        <h2 className="text-2xl font-black text-white tracking-tight">
          Invest in Your Next Senior Engineering Offer
        </h2>
        <p className="text-xs text-slate-400 mt-2">
          Candidates who practice on our adaptive FAANG simulators average a 34% higher offer valuation and 2.8x faster placement.
        </p>

        {/* Billing cycle toggle */}
        <div className="inline-flex items-center gap-2 p-1 rounded-xl bg-slate-950 border border-slate-800 mt-5">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              billingCycle === 'monthly' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              billingCycle === 'yearly' ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' : 'text-slate-400'
            }`}
          >
            <span>Yearly</span>
            <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-400">
              Save 25%
            </span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`rounded-2xl border p-6 flex flex-col justify-between transition-all relative ${
              plan.isPopular
                ? 'bg-slate-900/90 border-cyan-500/50 shadow-xl shadow-cyan-950/40 ring-1 ring-cyan-500/40 md:-translate-y-2'
                : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
            }`}
          >
            {plan.badge && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 text-[10px] font-extrabold uppercase tracking-wider shadow-md">
                {plan.badge}
              </div>
            )}

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-base font-bold text-white">{plan.name}</h3>
                {plan.isCurrent && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                    Active Plan
                  </span>
                )}
              </div>

              <div className="flex items-baseline gap-1 my-3">
                <span className="text-3xl font-black text-white">{plan.price}</span>
                <span className="text-xs text-slate-400">/{plan.period}</span>
              </div>

              <p className="text-xs text-slate-300 mb-5 leading-relaxed">{plan.description}</p>

              <div className="space-y-2.5 pt-4 border-t border-slate-800/80 mb-6">
                {plan.features.map((feature, fIdx) => (
                  <div key={fIdx} className="flex items-start gap-2.5 text-xs text-slate-300">
                    <Check className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                    <span className="leading-snug">{feature}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => onOpenPaymentModal(plan.id)}
              disabled={plan.isCurrent}
              className={`w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
                plan.isCurrent
                  ? 'bg-slate-800 text-slate-400 cursor-not-allowed border border-slate-700'
                  : plan.isPopular
                  ? 'bg-gradient-to-r from-cyan-400 to-blue-500 text-slate-950 hover:opacity-95 shadow-lg shadow-cyan-500/20'
                  : 'bg-slate-800 text-white hover:bg-slate-700 border border-slate-700'
              }`}
            >
              <span>{plan.cta}</span>
              {!plan.isCurrent && <ArrowRight className="w-3.5 h-3.5" />}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
