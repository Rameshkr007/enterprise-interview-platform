import Link from 'next/link'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'InterviewAI — Enterprise Mock Interview & ATS Analyzer',
}

export default function LandingPage() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navigation */}
      <nav className="flex items-center justify-between px-8 py-6 border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center">
            <span className="text-white text-xs font-bold">AI</span>
          </div>
          <span className="font-bold text-lg text-white">InterviewAI</span>
        </div>
        <div className="flex items-center gap-4">
          <Link href="/login" className="btn-ghost">Sign In</Link>
          <Link href="/register" className="btn-primary">Get Started</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-8 py-24 animate-fade-in">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-brand-500/30 bg-brand-500/10 text-brand-300 text-sm font-medium mb-8">
          <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse"></span>
          Powered by GPT-4o · LangGraph · PGVector
        </div>

        <h1 className="text-5xl md:text-7xl font-bold leading-tight mb-6 max-w-4xl">
          Ace Your Next Interview with
          <span className="gradient-text block mt-2">AI-Powered Coaching</span>
        </h1>

        <p className="text-xl text-slate-400 max-w-2xl mb-12 leading-relaxed">
          Semantic ATS resume scoring, adaptive AI interviews with real-time audio analytics,
          and personalized feedback — all in one enterprise-grade platform.
        </p>

        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link href="/register" className="btn-primary text-base px-8 py-4">
            Start Free Practice
          </Link>
          <Link href="/ats" className="btn-ghost text-base px-8 py-4">
            Analyze Resume
          </Link>
        </div>

        {/* Feature cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 w-full max-w-5xl">
          {[
            {
              icon: '&#x1F4CA;',
              title: 'Semantic ATS Scoring',
              desc: 'PGVector cosine similarity between your resume and job descriptions. No regex — true semantic understanding.',
            },
            {
              icon: '&#x1F3A4;',
              title: 'Adaptive AI Interviewer',
              desc: 'LangGraph state machine that adjusts difficulty in real-time based on your answer quality.',
            },
            {
              icon: '&#x1F4D1;',
              title: 'Native Audio Analytics',
              desc: 'Librosa & SciPy measure pitch variance, silence gaps, and filler words to coach your delivery.',
            },
          ].map((f) => (
            <div key={f.title} className="glass-card p-6 text-left">
              <div className="text-3xl mb-4" dangerouslySetInnerHTML={{ __html: f.icon }} />
              <h3 className="font-semibold text-white mb-2">{f.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/5 py-8 text-center text-slate-500 text-sm">
        &copy; {new Date().getFullYear()} InterviewAI. Built with FastAPI, LangGraph, PGVector.
      </footer>
    </div>
  )
}
