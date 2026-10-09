import Link from 'next/link'
import { Metadata } from 'next'
import ThreeIntelligenceCore from '@/components/3d/ThreeIntelligenceCore'
import SpatialCard from '@/components/ui/SpatialCard'

export const metadata: Metadata = {
  title: 'InterviewAI — Enterprise AI Career Intelligence & Mock Interview Platform',
  description:
    'Production-grade AI mock interview engine, semantic ATS resume vector scoring, and multi-turn career simulations with real-time biometric telemetry.',
}

export default function LandingPage() {
  const capabilityModules = [
    {
      href: '/ats',
      title: 'Semantic ATS Analyzer',
      description:
        'Computes 1536-dimensional PGVector cosine similarity between your resume and target job descriptions. Pinpoints exact semantic skill gaps without regex heuristics.',
      icon: '📊',
      badge: 'PGVector Core',
      accentColor: '#00f0ff',
      ctaText: 'Scan Resume Semantically',
      stat: '1536 Dimensions',
      statLabel: 'Vector Resolution',
    },
    {
      href: '/interview/new',
      title: 'Adaptive AI Mock Interview',
      description:
        'Stateful multi-turn interview driven by LangGraph state machines. Features real-time voice response, computer vision emotion analysis, and adaptive difficulty progression.',
      icon: '🎙️',
      badge: 'LangGraph v0.2',
      accentColor: '#8b5cf6',
      ctaText: 'Start Live Simulation',
      stat: '<120ms Latency',
      statLabel: 'Turn Orchestration',
    },
    {
      href: '/coding',
      title: 'AI Coding Interview',
      description:
        'In-browser collaborative code editor with real-time AI code review, algorithmic complexity analysis (Big-O), bug detection, and dynamic edge-case execution.',
      icon: '💻',
      badge: 'Algorithmic Engine',
      accentColor: '#38bdf8',
      ctaText: 'Launch Code Workspace',
      stat: 'Python / TS / C++',
      statLabel: 'Language Runtimes',
    },
    {
      href: '/system-design',
      title: 'System Design Interview',
      description:
        'Architect distributed systems under simulated senior interviewer scrutiny. Test trade-offs across sharding, caching, consensus, and fault-tolerance.',
      icon: '📐',
      badge: 'Architecture',
      accentColor: '#10b981',
      ctaText: 'Architect Systems',
      stat: 'Distributed Systems',
      statLabel: 'Design Rubrics',
    },
    {
      href: '/company-mode',
      title: 'Company-Specific Calibration',
      description:
        'Tailored interview rubrics for Google, Amazon (Leadership Principles), Meta, and Microsoft. Evaluates behavioral signals against real hiring committee standards.',
      icon: '🏢',
      badge: 'Tier-1 FAANG',
      accentColor: '#f59e0b',
      ctaText: 'Choose Target Company',
      stat: 'FAANG & Unicorns',
      statLabel: 'Hiring Rubrics',
    },
    {
      href: '/negotiation',
      title: 'Salary Negotiation Simulator',
      description:
        'Spar with an AI corporate compensation recruiter. Practice counter-offering base salary, RSUs, sign-on bonuses, and equity cliffs using real market percentiles.',
      icon: '💰',
      badge: 'Compensation AI',
      accentColor: '#ec4899',
      ctaText: 'Spar with HR Recruiter',
      stat: 'P25 — P90 Bands',
      statLabel: 'Market Calibration',
    },
    {
      href: '/resume-builder',
      title: 'AI Career Intelligence',
      description:
        'Transform raw experience bullet points into high-impact metric-driven achievements using STAR methodology and role-specific executive framing.',
      icon: '✨',
      badge: 'Career Synthesis',
      accentColor: '#06b6d4',
      ctaText: 'Refactor Resume',
      stat: 'STAR Framework',
      statLabel: 'Impact Structuring',
    },
    {
      href: '/job-tracker',
      title: 'Application Pipeline Tracker',
      description:
        'End-to-end telemetry Kanban board for tracking application lifecycles from initial contact to screening, onsite loops, and final offers.',
      icon: '💼',
      badge: 'Pipeline CRM',
      accentColor: '#f97316',
      ctaText: 'Manage Pipeline',
      stat: 'Full Lifecycle',
      statLabel: 'Kanban Workflow',
    },
    {
      href: '/daily-challenge',
      title: 'Daily Technical Challenge',
      description:
        'Keep interview muscle memory sharp with daily adaptive interview scenarios, spaced repetition algorithms (SM-2), and experience point progression.',
      icon: '🔥',
      badge: 'Spaced Repetition',
      accentColor: '#ef4444',
      ctaText: 'Solve Daily Problem',
      stat: 'SM-2 Algorithm',
      statLabel: 'Memory Retention',
    },
    {
      href: '/analytics',
      title: 'Analytics & Skill Intelligence',
      description:
        'Comprehensive multi-session performance telemetry including pitch stability, silence pause ratios, speech rate (WPM), and technical taxonomy mastery.',
      icon: '📈',
      badge: 'Acoustic & Semantic',
      accentColor: '#a855f7',
      ctaText: 'Inspect Performance',
      stat: '54 Telemetry Vectors',
      statLabel: 'Diagnostic Scope',
    },
  ]

  return (
    <div className="min-h-screen flex flex-col bg-[#07080c] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* ── Top Navigation Bar ───────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-white/5 bg-[#07080c]/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 via-indigo-500 to-violet-600 flex items-center justify-center shadow-[0_0_20px_rgba(0,240,255,0.3)]">
              <span className="text-black font-black text-sm tracking-wider">AI</span>
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight text-white">InterviewAI</span>
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30">
                  ENTERPRISE
                </span>
              </div>
              <span className="text-[11px] font-mono text-slate-500 block -mt-0.5">Career Intelligence Command</span>
            </div>
          </div>

          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#capabilities" className="hover:text-cyan-300 transition-colors">
              Capabilities
            </a>
            <a href="#architecture" className="hover:text-cyan-300 transition-colors">
              Architecture
            </a>
            <Link href="/ats" className="hover:text-cyan-300 transition-colors">
              ATS Analyzer
            </Link>
            <Link href="/coding" className="hover:text-cyan-300 transition-colors">
              Coding Round
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm font-medium text-slate-300 hover:text-white px-4 py-2 rounded-lg transition-colors"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="btn-cyan text-xs sm:text-sm py-2.5 px-5"
            >
              Get Started Free
            </Link>
          </div>
        </div>
      </header>

      {/* ── Immersive 3D Hero Section ───────────────────────────────────── */}
      <section className="relative pt-12 pb-24 md:py-28 overflow-hidden">
        {/* Atmospheric Glow Cones */}
        <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-gradient-to-b from-cyan-500/15 via-violet-600/10 to-transparent blur-[120px] pointer-events-none" />

        <div className="max-w-7xl mx-auto px-6 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center relative z-10">
          {/* Left Column: Headline & Action Prompts */}
          <div className="lg:col-span-7 flex flex-col items-start text-left">
            <div className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full border border-cyan-500/30 bg-cyan-950/40 text-cyan-300 text-xs font-mono mb-8 backdrop-blur-md">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse shadow-[0_0_10px_#00f0ff]" />
              LANGGRAPH 0.2 &bull; PGVECTOR 1536D &bull; ACOUSTIC ML
            </div>

            <h1 className="text-4xl sm:text-6xl md:text-7xl font-black tracking-tight leading-[1.08] mb-6 text-white">
              ENGINEER YOUR <br />
              <span className="gradient-text">NEXT CAREER MOVE.</span>
            </h1>

            <p className="text-lg sm:text-xl text-slate-400 max-w-xl mb-10 leading-relaxed font-normal">
              Analyze your skills. Practice adaptive AI interviews. Discover your gaps.
              Turn every practice session into measurable, production-grade career progress.
            </p>

            {/* Primary & Secondary Dual CTAs */}
            <div className="flex flex-wrap items-center gap-4 w-full sm:w-auto">
              <Link
                href="/interview/new"
                className="btn-cyan text-sm sm:text-base py-3.5 px-8 flex items-center justify-center gap-2 group shadow-[0_0_30px_rgba(0,240,255,0.3)]"
              >
                <span>Launch AI Interview</span>
                <span className="transform transition-transform group-hover:translate-x-1">→</span>
              </Link>

              <Link
                href="/ats"
                className="inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl border border-white/10 bg-white/[0.04] text-slate-200 hover:text-white hover:bg-white/[0.08] hover:border-cyan-400/40 transition-all text-sm sm:text-base font-semibold backdrop-blur-md"
              >
                <span>Analyze My Resume</span>
              </Link>
            </div>

            {/* Genuine Technical Infrastructure Badges */}
            <div className="mt-12 pt-8 border-t border-white/10 grid grid-cols-2 sm:grid-cols-4 gap-6 w-full text-left">
              <div>
                <div className="text-2xl font-black text-cyan-400 font-mono">1536d</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">Vector Embeddings</div>
              </div>
              <div>
                <div className="text-2xl font-black text-violet-400 font-mono">&lt;120ms</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">Graph Transition</div>
              </div>
              <div>
                <div className="text-2xl font-black text-emerald-400 font-mono">54 Vec</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">Acoustic Telemetry</div>
              </div>
              <div>
                <div className="text-2xl font-black text-amber-400 font-mono">10 AI</div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">Career Engines</div>
              </div>
            </div>
          </div>

          {/* Right Column: 3D AI Intelligence Core */}
          <div className="lg:col-span-5 relative w-full flex items-center justify-center">
            <div className="w-full max-w-[550px] aspect-square relative rounded-3xl border border-white/10 bg-radial-gradient from-cyan-950/20 via-black to-black/80 backdrop-blur-2xl shadow-[0_0_80px_rgba(0,0,0,0.8)] overflow-hidden">
              <ThreeIntelligenceCore />
            </div>
          </div>
        </div>
      </section>

      {/* ── Interactive Capability Universe (10 Modules) ──────────────────── */}
      <section id="capabilities" className="py-24 border-t border-white/5 relative">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-violet-500/10 text-violet-400 border border-violet-500/30 mb-4">
              CAPABILITY UNIVERSE
            </div>
            <h2 className="text-3xl sm:text-5xl font-black tracking-tight text-white mb-4">
              Integrated Career Intelligence Modules
            </h2>
            <p className="text-slate-400 text-base sm:text-lg">
              Ten purpose-built, production engines engineered to simulate every facet of modern technical hiring.
            </p>
          </div>

          {/* 10-Module Spatial Card Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilityModules.map((mod) => (
              <SpatialCard
                key={mod.title}
                href={mod.href}
                title={mod.title}
                description={mod.description}
                icon={mod.icon}
                badge={mod.badge}
                accentColor={mod.accentColor}
                ctaText={mod.ctaText}
                stat={mod.stat}
                statLabel={mod.statLabel}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── Real Architectural Engine Breakdown ──────────────────────────── */}
      <section id="architecture" className="py-24 border-t border-white/5 bg-[#090b12]/50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="max-w-2xl mb-16">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30 mb-4">
              SYSTEM ARCHITECTURE
            </div>
            <h2 className="text-3xl sm:text-4xl font-black tracking-tight text-white mb-4">
              Engineered on Production Foundations
            </h2>
            <p className="text-slate-400 text-sm sm:text-base">
              No superficial prompts or mock wrappers. Every simulation executes against verified FastAPI microservices and stateful vector pipelines.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="glass-command p-6">
              <div className="text-xs font-mono text-cyan-400 mb-2">PHASE 01 &bull; INGEST</div>
              <h3 className="text-lg font-bold text-white mb-2">Vector Ingestion</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                PyPDF extracts structural tokens, generating 1536-dimensional embeddings with OpenAI text-embedding-3-large stored directly in Supabase PGVector.
              </p>
            </div>

            <div className="glass-command p-6">
              <div className="text-xs font-mono text-violet-400 mb-2">PHASE 02 &bull; GRAPH</div>
              <h3 className="text-lg font-bold text-white mb-2">LangGraph Machine</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Multi-turn state graphs dynamically calibrate question difficulty, branch based on candidate confidence, and maintain deterministic memory checkpoints.
              </p>
            </div>

            <div className="glass-command p-6">
              <div className="text-xs font-mono text-emerald-400 mb-2">PHASE 03 &bull; TELEMETRY</div>
              <h3 className="text-lg font-bold text-white mb-2">Acoustic Analysis</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Native Librosa and SciPy compute pitch variance (f0 PYIN), silence ratios, and filler word frequency alongside Whisper audio transcription.
              </p>
            </div>

            <div className="glass-command p-6">
              <div className="text-xs font-mono text-amber-400 mb-2">PHASE 04 &bull; DIAGNOSTIC</div>
              <h3 className="text-lg font-bold text-white mb-2">Executive Scorecard</h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Synthesizes strengths, architectural deficiencies, and personalized learning roadmaps with percentile benchmark rankings.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── Call to Action Banner ────────────────────────────────────────── */}
      <section className="py-20 border-t border-white/5 relative overflow-hidden">
        <div className="absolute inset-0 bg-radial-gradient from-cyan-500/10 via-transparent to-transparent pointer-events-none" />
        <div className="max-w-4xl mx-auto px-6 text-center relative z-10">
          <h2 className="text-3xl sm:text-5xl font-black text-white tracking-tight mb-6">
            Ready to Accelerate Your Career?
          </h2>
          <p className="text-slate-400 text-base sm:text-lg mb-8 max-w-xl mx-auto">
            Experience the difference of structured, AI-assisted career simulations backed by true vector telemetry.
          </p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <Link href="/register" className="btn-cyan py-3.5 px-8 text-base">
              Create Free Account
            </Link>
            <Link href="/ats" className="btn-ghost py-3.5 px-8 text-base">
              Try ATS Resume Analyzer
            </Link>
          </div>
        </div>
      </section>

      {/* ── Footer ──────────────────────────────────────────────────────── */}
      <footer className="border-t border-white/5 py-10 bg-[#050609] text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="font-mono text-slate-400">All Systems Operational &bull; Render + Vercel + Supabase PGVector</span>
          </div>
          <div>
            &copy; {new Date().getFullYear()} InterviewAI Platform. Enterprise Career Intelligence.
          </div>
        </div>
      </footer>
    </div>
  )
}
