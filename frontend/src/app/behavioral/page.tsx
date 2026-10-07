'use client'

import React, { useState, useEffect } from 'react'
import { behavioralApi } from '@/lib/api'
import type {
  BehavioralQuestion,
  LeadershipCompetency,
  STARBehavioralEvaluation,
  FollowUpProbe,
  STARReframeResponse,
} from '@/lib/types'

export default function BehavioralStudioPage() {
  const [competencies, setCompetencies] = useState<LeadershipCompetency[]>([])
  const [selectedComp, setSelectedComp] = useState<string>('ownership')
  const [questions, setQuestions] = useState<BehavioralQuestion[]>([])
  const [selectedQuestion, setSelectedQuestion] = useState<BehavioralQuestion | null>(null)
  const [answerTranscript, setAnswerTranscript] = useState<string>('')
  
  // Real-time I/We calculation
  const [iCount, setICount] = useState<number>(0)
  const [weCount, setWeCount] = useState<number>(0)
  const [ratio, setRatio] = useState<number>(0.5)

  // Loading & evaluation state
  const [isEvaluating, setIsEvaluating] = useState<boolean>(false)
  const [evalResult, setEvalResult] = useState<STARBehavioralEvaluation | null>(null)
  const [followUpProbes, setFollowUpProbes] = useState<FollowUpProbe[]>([])
  const [isLoadingProbes, setIsLoadingProbes] = useState<boolean>(false)
  const [reframedStory, setReframedStory] = useState<STARReframeResponse | null>(null)
  const [isReframing, setIsReframing] = useState<boolean>(false)
  const [errorMsg, setErrorMsg] = useState<string | null>(null)

  // Load competencies and questions on mount
  useEffect(() => {
    async function loadData() {
      try {
        const comps = await behavioralApi.getCompetencies()
        setCompetencies(comps)
        const qs = await behavioralApi.getQuestions('ownership')
        setQuestions(qs)
        if (qs.length > 0) {
          setSelectedQuestion(qs[0])
        }
      } catch (err: unknown) {
        console.error('Failed to load behavioral data', err)
      }
    }
    loadData()
  }, [])

  // Load questions when competency changes
  const handleCompetencyChange = async (comp: string) => {
    setSelectedComp(comp)
    try {
      const qs = await behavioralApi.getQuestions(comp)
      setQuestions(qs)
      if (qs.length > 0) {
        setSelectedQuestion(qs[0])
      }
    } catch (err: unknown) {
      console.error('Failed to filter questions', err)
    }
  }

  // Real-time ownership pronoun tracking
  const handleAnswerChange = (text: string) => {
    setAnswerTranscript(text)
    const iMatches = text.match(/\b(i|me|my|mine|myself|i'd|i've|i'll|i'm)\b/gi) || []
    const weMatches = text.match(/\b(we|us|our|ours|ourselves|we'd|we've|we'll|we're)\b/gi) || []
    const total = iMatches.length + weMatches.length
    setICount(iMatches.length)
    setWeCount(weMatches.length)
    setRatio(total === 0 ? 0.5 : iMatches.length / total)
  }

  // Evaluate STAR
  const handleEvaluate = async () => {
    if (!selectedQuestion || answerTranscript.trim().length < 20) {
      setErrorMsg('Please enter at least 20 characters for your response before evaluating.')
      return
    }
    setErrorMsg(null)
    setIsEvaluating(true)
    try {
      const res = await behavioralApi.evaluateSTAR({
        question: selectedQuestion.question,
        answer_transcript: answerTranscript,
        competency: selectedComp,
      })
      setEvalResult(res)
    } catch (err: unknown) {
      setErrorMsg('Failed to evaluate STAR response. Please check backend connection.')
    } finally {
      setIsEvaluating(false)
    }
  }

  // Generate Bar-Raiser Probes
  const handleGenerateProbes = async () => {
    if (!selectedQuestion || answerTranscript.trim().length < 20) return
    setIsLoadingProbes(true)
    try {
      const res = await behavioralApi.generateProbes({
        question: selectedQuestion.question,
        answer_transcript: answerTranscript,
        competency: selectedComp,
      })
      setFollowUpProbes(res.probes)
    } catch (err: unknown) {
      console.error('Failed to generate probes', err)
    } finally {
      setIsLoadingProbes(false)
    }
  }

  // Reframe story
  const handleReframe = async () => {
    if (!selectedQuestion || answerTranscript.trim().length < 20) return
    setIsReframing(true)
    try {
      const res = await behavioralApi.reframeStory({
        question: selectedQuestion.question,
        raw_answer: answerTranscript,
        competency: selectedComp,
      })
      setReframedStory(res)
    } catch (err: unknown) {
      console.error('Failed to reframe story', err)
    } finally {
      setIsReframing(false)
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10 font-sans">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <div className="border-b border-slate-800 pb-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800/60 mb-2">
                Phase 11 Engine
              </div>
              <h1 className="text-3xl font-extrabold tracking-tight text-white">
                Executive Behavioral & STAR+L Studio
              </h1>
              <p className="text-sm text-slate-400 mt-1">
                Amazon Leadership Principles, Google Structured Rubrics, Real-Time Ownership Meter ($I/We$), and Bar-Raiser Follow-Up Simulator.
              </p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
                Framework: <strong className="text-white">STAR + Learnings</strong>
              </span>
            </div>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-xl bg-red-950/80 border border-red-800 text-red-300 text-sm flex items-center justify-between">
            <span>{errorMsg}</span>
            <button onClick={() => setErrorMsg(null)} className="text-red-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Competency & Question Selector */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">Leadership Competency</h2>
            <div className="flex flex-wrap gap-2">
              {competencies.map((comp) => (
                <button
                  key={comp.id}
                  onClick={() => handleCompetencyChange(comp.id)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all ${
                    selectedComp === comp.id
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                      : 'bg-slate-800/80 text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {comp.title}
                </button>
              ))}
            </div>

            <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 pt-4 border-t border-slate-800">
              Select Question
            </h2>
            <div className="space-y-2 max-h-[300px] overflow-y-auto pr-1">
              {questions.map((q) => (
                <div
                  key={q.id}
                  onClick={() => setSelectedQuestion(q)}
                  className={`p-3 rounded-xl cursor-pointer border text-xs transition-all ${
                    selectedQuestion?.id === q.id
                      ? 'bg-blue-950/60 border-blue-600/80 text-white shadow-md'
                      : 'bg-slate-900 border-slate-800/80 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <p className="font-semibold">{q.title}</p>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{q.question}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Active Question & Live Ownership Meter */}
          <div className="lg:col-span-2 space-y-6">
            {selectedQuestion && (
              <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <span className="text-xs font-mono uppercase text-blue-400 font-bold tracking-wide">
                      {selectedQuestion.competency.replace('_', ' ')}
                    </span>
                    <h3 className="text-xl font-bold text-white mt-1">{selectedQuestion.title}</h3>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-200 text-sm leading-relaxed">
                  {selectedQuestion.question}
                </div>

                {selectedQuestion.evaluation_criteria && selectedQuestion.evaluation_criteria.length > 0 && (
                  <div className="flex flex-wrap gap-2 pt-1">
                    {selectedQuestion.evaluation_criteria.map((crit, idx) => (
                      <span key={idx} className="text-[11px] px-2.5 py-1 rounded-md bg-slate-800/80 text-slate-300 border border-slate-700/60">
                        ✓ {crit}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Answer Input Canvas */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <label className="text-sm font-bold uppercase tracking-wider text-slate-300">
                  Your Answer Transcript (STAR+L Format)
                </label>
                <div className="text-xs text-slate-400">
                  Words: <strong className="text-white">{answerTranscript.split(/\s+/).filter(Boolean).length}</strong>
                </div>
              </div>

              <textarea
                value={answerTranscript}
                onChange={(e) => handleAnswerChange(e.target.value)}
                placeholder="Structure your story with Situation, Task, Action (emphasizing YOUR personal contribution), Result (quantified business metrics), and Learning/Retrospective reflection..."
                rows={8}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 p-4 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500/50 leading-relaxed resize-y"
              />

              {/* Live I vs We Ownership Meter */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-300">
                    Live Pronoun Ownership Meter: <span className="text-white font-bold">{Math.round(ratio * 100)}% Individual</span>
                  </span>
                  <span className="text-slate-400">
                    <strong>{iCount}</strong> &apos;I&apos; vs <strong>{weCount}</strong> &apos;We&apos;
                  </span>
                </div>
                <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex">
                  <div
                    className={`h-full transition-all duration-300 ${
                      ratio >= 0.58 ? 'bg-emerald-500' : ratio >= 0.35 ? 'bg-blue-500' : 'bg-amber-500'
                    }`}
                    style={{ width: `${Math.min(Math.max(ratio * 100, 5), 95)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  {ratio >= 0.58
                    ? '🎯 Strong individual ownership. Clear personal attribution.'
                    : ratio >= 0.35
                    ? '⚖️ Balanced collaborative framing. Ensure your personal role is distinctly highlighted.'
                    : '⚠️ High team-attribution. Bar-raisers will probe: What was YOUR specific personal contribution?'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={handleEvaluate}
                  disabled={isEvaluating}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/30 transition-all disabled:opacity-50"
                >
                  {isEvaluating ? 'Evaluating STAR+L...' : '🚀 Evaluate Response'}
                </button>
                <button
                  onClick={handleGenerateProbes}
                  disabled={isLoadingProbes || !answerTranscript.trim()}
                  className="px-4 py-2.5 rounded-xl bg-purple-900/60 hover:bg-purple-800/80 border border-purple-700/80 text-purple-200 font-semibold text-sm transition-all disabled:opacity-50"
                >
                  {isLoadingProbes ? 'Generating Probes...' : '🔍 Bar-Raiser Follow-Up Probes'}
                </button>
                <button
                  onClick={handleReframe}
                  disabled={isReframing || !answerTranscript.trim()}
                  className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-sm border border-slate-700 transition-all disabled:opacity-50"
                >
                  {isReframing ? 'Reframing...' : '✨ Executive STAR Reframe'}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Evaluation Results Card */}
        {evalResult && (
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
              <div>
                <span className="text-xs uppercase tracking-wider text-slate-400 font-bold">Bar-Raiser Verdict</span>
                <div className="flex items-center gap-3 mt-1">
                  <span className={`text-2xl font-extrabold ${
                    evalResult.bar_raiser_verdict.includes('Hire') && !evalResult.bar_raiser_verdict.includes('No')
                      ? 'text-emerald-400'
                      : 'text-amber-400'
                  }`}>
                    {evalResult.bar_raiser_verdict}
                  </span>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-200 border border-slate-700">
                    Score: {evalResult.overall_score}/100
                  </span>
                </div>
              </div>
              <div className="text-sm text-slate-400 text-right">
                <div>Ownership: <strong className="text-white">{evalResult.ownership_metrics.ownership_level}</strong></div>
                <div>Quantified Metrics: <strong className="text-emerald-400">{evalResult.quantifiable_metrics_found.length} detected</strong></div>
              </div>
            </div>

            {/* 5-Step STAR+L Breakdown */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">STAR + Learnings Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {['situation', 'task', 'action', 'result', 'learning'].map((k) => {
                  const item = evalResult.star_breakdown[k]
                  if (!item) return null
                  return (
                    <div key={k} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold uppercase text-blue-400">{item.name}</span>
                        <span className="text-xs font-mono font-bold text-slate-300">{item.score}</span>
                      </div>
                      <p className="text-xs text-slate-300 line-clamp-3">{item.content || 'N/A'}</p>
                      <p className="text-[11px] text-slate-400 italic">{item.feedback}</p>
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Competency Radar Breakdown */}
            {evalResult.competency_scores && (
              <div className="space-y-3 pt-2">
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-300">Competency Mapping</h3>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                  {Object.entries(evalResult.competency_scores).map(([comp, sc]) => (
                    <div key={comp} className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 text-center">
                      <div className="text-xs text-slate-400 uppercase font-semibold">{comp.replace(/_/g, ' ')}</div>
                      <div className="text-lg font-bold text-white mt-1">{sc}/100</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Bar-Raiser Follow-Up Probes Drawer */}
        {followUpProbes.length > 0 && (
          <div className="bg-slate-900/90 border border-purple-900/60 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center gap-2">
              <span className="text-purple-400 text-xl">🔍</span>
              <h3 className="text-lg font-bold text-white">Bar-Raiser Follow-Up Probes</h3>
            </div>
            <p className="text-xs text-slate-400">
              High-pressure inquiries generated directly from the weak points and ambiguities identified in your answer:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {followUpProbes.map((probe, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-950 border border-purple-900/40 space-y-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800/60">
                    {probe.probe_type}
                  </span>
                  <p className="text-sm font-semibold text-slate-100">{probe.question}</p>
                  <p className="text-xs text-slate-400 italic">Intent: {probe.rationale}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Executive STAR Reframe Drawer */}
        {reframedStory && (
          <div className="bg-slate-900/90 border border-blue-900/60 rounded-2xl p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-blue-400 text-xl">✨</span>
                <h3 className="text-lg font-bold text-white">Executive STAR+L Story Reframe</h3>
              </div>
              <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-950 text-emerald-400 border border-emerald-800">
                Estimated Lift: {reframedStory.bar_raiser_score_uplift}
              </span>
            </div>
            <div className="p-5 rounded-xl bg-slate-950 border border-slate-800 text-sm leading-relaxed text-slate-200 whitespace-pre-line font-mono">
              {reframedStory.reframed_story}
            </div>
            <div className="space-y-1 pt-2">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Key Enhancements Made:</h4>
              <ul className="list-disc list-inside text-xs text-slate-300 space-y-1">
                {reframedStory.key_enhancements.map((enh, idx) => (
                  <li key={idx}>{enh}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
