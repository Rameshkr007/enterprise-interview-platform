'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { useInterviewStore } from '@/store/interview'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAudioCapture } from '@/hooks/useAudioCapture'
import { useAuthStore } from '@/store/auth'
import { authApi, interviewApi } from '@/lib/api'
import type { HintResponse, ExplanationResponse, WsMessage } from '@/lib/types'

import { AIInterviewerAvatar } from '@/components/interview/AIInterviewerAvatar'
import { WebcamEmotionTracker } from '@/components/interview/WebcamEmotionTracker'
import { TTSPlayer } from '@/components/interview/TTSPlayer'
import { EmotionMeter } from '@/components/interview/EmotionMeter'
import { CoachWhisper } from '@/components/interview/CoachWhisper'
import {
  Lightbulb,
  BookOpen,
  Pause,
  Play,
  Video,
  VideoOff,
  Mic,
  MicOff,
  ShieldCheck,
  X,
  Sparkles,
  Send,
  Code2,
  AlertCircle,
  Clock,
  Layers,
  ChevronRight,
  HelpCircle,
  FileText,
} from 'lucide-react'

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const map: Record<string, string> = {
    easy: 'px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/15 border border-emerald-500/30 text-emerald-300',
    medium: 'px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-500/15 border border-cyan-500/30 text-cyan-300',
    hard: 'px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/15 border border-amber-500/30 text-amber-300',
    expert: 'px-2 py-0.5 rounded-full text-xs font-mono font-bold bg-rose-500/15 border border-rose-500/30 text-rose-300',
  }
  return <span className={map[difficulty] ?? 'px-2 py-0.5 rounded-full text-xs font-mono bg-cyan-500/10 text-cyan-300'}>{difficulty}</span>
}

export default function InterviewRoomPage() {
  const params = useParams()
  const sessionId = params?.sessionId as string
  const router = useRouter()

  const { access_token } = useAuthStore()
  const {
    currentQuestion,
    partialTranscript,
    isRecording,
    isProcessing,
    isComplete,
    setRecording,
    setProcessing,
    handleWsMessage,
    reset,
  } = useInterviewStore()

  const [connected, setConnected] = useState(false)
  const [wsError, setWsError] = useState<string | null>(null)
  const [recordingTime, setRecordingTime] = useState(0)
  const [isAiSpeaking, setIsAiSpeaking] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Session Preferences from Wizard
  const [sessionPrefs, setSessionPrefs] = useState<{
    mode: 'practice' | 'exam'
    allow_hints: boolean
    target_role?: string
  }>({ mode: 'practice', allow_hints: true })

  // Session Lifecycle: Pause / Active Timers
  const [isPaused, setIsPaused] = useState(false)
  const [sessionElapsedSeconds, setSessionElapsedSeconds] = useState(0)
  const sessionTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Informed Consent & Device Check Modal
  const [hasConsented, setHasConsented] = useState<boolean | null>(null)
  const [consentChoice, setConsentChoice] = useState<'video_audio' | 'audio_only' | 'no_recording'>('video_audio')
  const [showConsentModal, setShowConsentModal] = useState(true)

  // MediaRecorder for Continuous Background Video Chunk Upload
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const segmentIndexRef = useRef(0)
  const [isMediaRecording, setIsMediaRecording] = useState(false)
  const [uploadedSegmentsCount, setUploadedSegmentsCount] = useState(0)

  // AI Tutor State (Hints & Explanations)
  const [hintData, setHintData] = useState<HintResponse | null>(null)
  const [explanationData, setExplanationData] = useState<ExplanationResponse | null>(null)
  const [isFetchingHint, setIsFetchingHint] = useState(false)
  const [isFetchingExplanation, setIsFetchingExplanation] = useState(false)
  const [showTutorDrawer, setShowTutorDrawer] = useState(false)

  // Optional Text Answer Mode
  const [textAnswerMode, setTextAnswerMode] = useState(false)
  const [typedAnswer, setTypedAnswer] = useState('')
  const [isSubmittingText, setIsSubmittingText] = useState(false)

  // Audio metrics for delivery meter
  const [audioMetrics, setAudioMetrics] = useState({
    silenceRatio: 0.12,
    pitchVarianceScore: 0.65,
    fillerWordRate: 1.2,
    speechRateWpm: 135,
  })

  // Load preferences from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && sessionId) {
      const stored = localStorage.getItem(`session_prefs_${sessionId}`)
      if (stored) {
        try {
          const parsed = JSON.parse(stored)
          setSessionPrefs({
            mode: parsed.mode || 'practice',
            allow_hints: parsed.allow_hints !== false,
            target_role: parsed.target_role,
          })
        } catch {}
      }
    }
  }, [sessionId])

  // Session Active Timer
  useEffect(() => {
    if (!isPaused && !isComplete) {
      sessionTimerRef.current = setInterval(() => {
        setSessionElapsedSeconds((s) => s + 1)
      }, 1000)
    }
    return () => {
      if (sessionTimerRef.current) clearInterval(sessionTimerRef.current)
    }
  }, [isPaused, isComplete])

  const handleAutoReauth = useCallback(async () => {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null
    if (!refreshToken) {
      router.push(`/login?redirect=/interview/${sessionId}`)
      return
    }
    try {
      const tokens = await authApi.refresh(refreshToken)
      localStorage.setItem('access_token', tokens.access_token)
      localStorage.setItem('refresh_token', tokens.refresh_token)
      useAuthStore.setState({ access_token: tokens.access_token, refresh_token: tokens.refresh_token })
      setWsError(null)
      connect(sessionId, tokens.access_token)
    } catch {
      setWsError('Your login session has expired. Please log in again.')
    }
  }, [sessionId, router])

  const onWsMessage = useCallback(
    (msg: WsMessage) => {
      handleWsMessage(msg)
      if (msg.type === 'error') {
        const errorText = (msg.payload?.message as string) || 'Connection error'
        setWsError(errorText)
        if (
          msg.payload?.code === 'UNAUTHORIZED' ||
          errorText.toLowerCase().includes('auth') ||
          errorText.toLowerCase().includes('token')
        ) {
          handleAutoReauth()
        }
      } else if (msg.type === 'question') {
        setWsError(null)
        setIsAiSpeaking(true)
        // Reset turn-level tutor cards
        setHintData(null)
        setExplanationData(null)
        setTypedAnswer('')
        if (msg.payload.audio_metrics) {
          const m = msg.payload.audio_metrics as Record<string, number>
          setAudioMetrics({
            silenceRatio: m.silence_ratio || 0.1,
            pitchVarianceScore: m.pitch_variance_score || 0.5,
            fillerWordRate: m.filler_word_rate || 0,
            speechRateWpm: m.speech_rate_wpm || 130,
          })
        }
      }
    },
    [handleWsMessage, handleAutoReauth]
  )

  const { status, connect, sendAudioChunk, sendAudioEnd } = useWebSocket(onWsMessage)
  const { startRecording, stopRecording, error: audioError } = useAudioCapture()

  useEffect(() => {
    const token = (typeof window !== 'undefined' ? localStorage.getItem('access_token') : null) || access_token
    if (!token) {
      router.push(`/login?redirect=/interview/${sessionId}`)
      return
    }

    if (sessionId) {
      connect(sessionId, token)
      setConnected(true)
    }
    return () => reset()
  }, [access_token, sessionId, connect, reset, router])

  useEffect(() => {
    if (status === 'connected') setConnected(true)
    if (status === 'error') setWsError('WebSocket connection failed')
  }, [status])

  // Consent & Background Video MediaRecorder setup
  async function handleConfirmConsent() {
    setHasConsented(true)
    setShowConsentModal(false)

    if (consentChoice === 'video_audio' || consentChoice === 'audio_only') {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: consentChoice === 'video_audio',
          audio: true,
        })

        const recorder = new MediaRecorder(stream, { mimeType: 'video/webm' })
        mediaRecorderRef.current = recorder

        recorder.ondataavailable = async (e) => {
          if (e.data && e.data.size > 0) {
            const currentIdx = segmentIndexRef.current++
            const reader = new FileReader()
            reader.onloadend = async () => {
              const b64 = (reader.result as string).split(',')[1]
              if (b64) {
                try {
                  await interviewApi.uploadRecordingSegment({
                    session_id: sessionId,
                    segment_index: currentIdx,
                    duration_s: 10.0,
                    data_b64: b64,
                    media_type: 'video/webm',
                  })
                  setUploadedSegmentsCount((c) => c + 1)
                } catch {}
              }
            }
            reader.readAsDataURL(e.data)
          }
        }

        recorder.start(10000) // 10 second timeslice segments
        setIsMediaRecording(true)
      } catch {
        // Fallback to audio only if camera unavailable
        setIsMediaRecording(false)
      }
    }
  }

  // Answer Audio Recording Handlers
  async function handleStartRecording() {
    if (isPaused) return
    setIsAiSpeaking(false)
    setRecording(true)
    setRecordingTime(0)
    timerRef.current = setInterval(() => setRecordingTime((t) => t + 1), 1000)
    await startRecording((chunk) => sendAudioChunk(chunk))
  }

  async function handleStopRecording() {
    if (timerRef.current) clearInterval(timerRef.current)
    setRecording(false)
    setProcessing(true)
    await stopRecording()
    sendAudioEnd()
  }

  // Direct Text Answer Submission
  async function handleSubmitTextAnswer() {
    if (!typedAnswer.trim() || isProcessing) return
    setIsSubmittingText(true)
    setProcessing(true)

    try {
      const res = await interviewApi.submitAnswer({
        session_id: sessionId,
        turn_index: currentQuestion?.turn_index ?? 0,
        answer_text: typedAnswer.trim(),
      })

      setTypedAnswer('')
      setTextAnswerMode(false)
      // Process next question directly
      handleWsMessage({
        type: res.is_complete ? 'complete' : 'question',
        payload: {
          text: res.question_text,
          category: res.category,
          difficulty: res.difficulty,
          turn_index: res.turn_index,
        },
      })
    } catch (err: any) {
      setWsError(err?.response?.data?.detail || 'Failed to submit text answer.')
    } finally {
      setIsSubmittingText(false)
      setProcessing(false)
    }
  }

  // Session Pause / Resume
  async function handleTogglePause() {
    const nextPaused = !isPaused
    setIsPaused(nextPaused)
    try {
      await interviewApi.pauseSession(sessionId, nextPaused ? 'pause' : 'resume', sessionElapsedSeconds)
    } catch {}
  }

  // Tutor: Request Progressive Hint
  async function handleRequestHint() {
    if (!currentQuestion) return
    setIsFetchingHint(true)
    setShowTutorDrawer(true)
    try {
      const res = await interviewApi.getHint(sessionId, {
        turn_index: currentQuestion.turn_index ?? 0,
        current_question: currentQuestion.text,
        topic: currentQuestion.category,
      })
      setHintData(res)
    } catch {
      setHintData({
        hint: 'Examine the problem invariants. What data structure choice minimizes lookup complexity under constraints?',
        level: 1,
        pedagogical_guidance: 'Break down subproblems step-by-step.',
      })
    } finally {
      setIsFetchingHint(false)
    }
  }

  // Tutor: Request Conceptual Explanation
  async function handleRequestExplanation() {
    if (!currentQuestion) return
    setIsFetchingExplanation(true)
    setShowTutorDrawer(true)
    try {
      const res = await interviewApi.getExplanation(sessionId, {
        turn_index: currentQuestion.turn_index ?? 0,
        current_question: currentQuestion.text,
        topic: currentQuestion.category,
      })
      setExplanationData(res)
    } catch {
      setExplanationData({
        core_concept: `Core architectural principles of ${currentQuestion.category}.`,
        model_answer: 'A high-scoring answer clearly articulates trade-offs, state bounds, and failure modes.',
        key_takeaways: ['State assumptions upfront', 'Quantify space/time bounds', 'Handle edge conditions'],
        common_pitfalls: ['Ignoring boundary limits', 'Vague complexity estimates'],
      })
    } finally {
      setIsFetchingExplanation(false)
    }
  }

  // Completed Screen
  if (isComplete) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-8 animate-fade-in px-6 bg-[#070814] text-slate-100">
        <div className="w-20 h-20 rounded-3xl bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center text-4xl shadow-2xl">
          🎉
        </div>
        <div className="text-center space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-white">Interview Complete!</h1>
          <p className="text-slate-400 max-w-md mx-auto text-sm leading-relaxed">
            Your responses, acoustic delivery features, and multi-agent rubric evaluations have been compiled into an evidence-based report.
          </p>
        </div>
        <div className="flex gap-4">
          <button
            id="view-report-btn"
            onClick={() => router.push(`/report/${sessionId}`)}
            className="px-8 py-3.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold transition-all shadow-xl shadow-cyan-500/25 cursor-pointer flex items-center gap-2"
          >
            <span>View Full Report &amp; Replay</span>
            <ChevronRight className="w-4 h-4" />
          </button>
          <button
            onClick={() => router.push('/dashboard')}
            className="px-6 py-3.5 rounded-2xl bg-white/[0.05] border border-white/[0.1] hover:bg-white/[0.1] text-white font-semibold transition-all cursor-pointer"
          >
            Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col max-w-7xl mx-auto px-4 sm:px-6 py-6 animate-fade-in space-y-6 bg-[#070814] text-slate-100">
      {/* Real-time Coach Whisper */}
      <CoachWhisper
        silenceSeconds={recordingTime > 6 ? 5 : 0}
        fillerCount={Math.floor(audioMetrics.fillerWordRate * 2)}
        isSpeaking={isRecording}
      />

      {/* Top Header Bar */}
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div
            className={`w-3 h-3 rounded-full ${
              connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
            }`}
          />
          <div>
            <div className="text-slate-200 font-bold text-sm flex items-center gap-2">
              <span>{sessionPrefs.target_role || 'Live AI Technical Session'}</span>
              <span className="px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/20 text-cyan-300 font-mono">
                {sessionPrefs.mode === 'practice' ? '💡 Practice Mode' : '🔒 Proctored Exam'}
              </span>
            </div>
            <div className="text-[11px] text-slate-400 font-mono flex items-center gap-2">
              <span>Active Time: {Math.floor(sessionElapsedSeconds / 60)}m {sessionElapsedSeconds % 60}s</span>
              {isPaused && <span className="text-amber-400 font-bold">(PAUSED)</span>}
              {isMediaRecording && <span className="text-rose-400 font-semibold">• Video Recording Active</span>}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5">
          {/* Pause / Resume Session Button */}
          <button
            type="button"
            onClick={handleTogglePause}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold font-mono flex items-center gap-1.5 cursor-pointer transition-all ${
              isPaused
                ? 'bg-amber-500/20 border-amber-500/40 text-amber-300 hover:bg-amber-500/30'
                : 'bg-white/[0.04] border-white/[0.1] text-slate-300 hover:text-white'
            }`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5 text-amber-400" /> : <Pause className="w-3.5 h-3.5" />}
            <span>{isPaused ? 'Resume' : 'Pause'}</span>
          </button>

          {currentQuestion && (
            <DifficultyBadge difficulty={currentQuestion.difficulty} />
          )}

          <button
            onClick={() => router.push('/dashboard')}
            className="px-3.5 py-1.5 rounded-xl bg-white/[0.04] border border-white/[0.08] hover:border-white/[0.2] text-xs font-semibold text-slate-300 hover:text-white transition-all cursor-pointer"
          >
            Exit
          </button>
        </div>
      </div>

      {/* Paused Overlay Alert */}
      {isPaused && (
        <div className="p-4 rounded-2xl bg-amber-500/15 border border-amber-500/30 text-amber-300 text-sm flex items-center justify-between animate-fade-in">
          <div className="flex items-center gap-3">
            <Clock className="w-5 h-5 text-amber-400 shrink-0" />
            <div>
              <span className="font-bold">Session Paused.</span> Questions and recording timers are halted.
            </div>
          </div>
          <button
            type="button"
            onClick={handleTogglePause}
            className="px-4 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs cursor-pointer transition-all shadow-md"
          >
            Resume Interview
          </button>
        </div>
      )}

      {/* Error Alert */}
      {(wsError || audioError) && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
          <div className="flex items-center gap-2.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400 animate-pulse shrink-0" />
            <span className="leading-snug">{wsError || audioError}</span>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={handleAutoReauth}
              className="px-3.5 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-200 text-xs font-bold border border-rose-500/40 transition-colors cursor-pointer"
            >
              Reconnect
            </button>
          </div>
        </div>
      )}

      {/* Main Dual Stage: AI Interviewer & Candidate Arena */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Side: 3D AI Interviewer & Vision HUD */}
        <div className="lg:col-span-5 flex flex-col gap-5">
          {/* Holographic AI Interviewer */}
          <AIInterviewerAvatar
            isSpeaking={isAiSpeaking}
            isListening={isRecording}
            difficulty={currentQuestion?.difficulty || 'medium'}
            interviewerName="Agent Nova"
          />

          {/* Computer Vision & Posture Tracker */}
          <WebcamEmotionTracker />
        </div>

        {/* Right Side: Active Question, Voice/Text Synthesis & Recording Area */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          {/* Question Presentation Card */}
          <div className="p-6 sm:p-8 rounded-3xl border border-white/10 bg-slate-900/60 shadow-xl space-y-4 backdrop-blur-xl">
            <div className="flex items-center justify-between">
              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 capitalize">
                {currentQuestion?.category || 'Technical Assessment'}
              </span>
              <span className="text-slate-400 text-xs font-mono font-semibold">
                Turn #{(currentQuestion?.turn_index ?? 0) + 1}
              </span>
            </div>

            {currentQuestion ? (
              <p className="text-lg sm:text-xl font-medium text-white leading-relaxed">
                {currentQuestion.text}
              </p>
            ) : (
              <div className="space-y-2">
                <div className="skeleton w-3/4 h-6" />
                <div className="skeleton w-1/2 h-6" />
              </div>
            )}

            {/* TTS Audio Voice Output Player */}
            {currentQuestion && (
              <TTSPlayer
                text={currentQuestion.text}
                voice="nova"
                autoPlay={true}
                onStarted={() => setIsAiSpeaking(true)}
                onEnded={() => setIsAiSpeaking(false)}
              />
            )}

            {/* AI Tutor Actions in Practice Mode */}
            {sessionPrefs.allow_hints && (
              <div className="pt-2 border-t border-white/[0.06] flex items-center gap-3">
                <button
                  type="button"
                  onClick={handleRequestHint}
                  disabled={isFetchingHint || !currentQuestion}
                  className="px-3.5 py-1.5 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 hover:bg-amber-500/25 text-xs font-bold font-mono flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                  <span>{isFetchingHint ? 'Synthesizing...' : '💡 Request Hint'}</span>
                </button>

                <button
                  type="button"
                  onClick={handleRequestExplanation}
                  disabled={isFetchingExplanation || !currentQuestion}
                  className="px-3.5 py-1.5 rounded-xl bg-indigo-500/15 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-500/25 text-xs font-bold font-mono flex items-center gap-1.5 transition-all cursor-pointer"
                >
                  <BookOpen className="w-3.5 h-3.5 text-indigo-400" />
                  <span>{isFetchingExplanation ? 'Analyzing...' : '📖 Explain Concept'}</span>
                </button>
              </div>
            )}
          </div>

          {/* AI Tutor Floating Drawer / Card */}
          {showTutorDrawer && (hintData || explanationData) && (
            <div className="p-5 rounded-3xl bg-slate-900/90 border border-amber-500/40 shadow-2xl space-y-4 animate-fade-in relative">
              <button
                type="button"
                onClick={() => setShowTutorDrawer(false)}
                className="absolute top-4 right-4 text-slate-400 hover:text-white cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400">
                <Sparkles className="w-4 h-4" />
                <span>AI TUTOR COPILOT DEBRIEF</span>
              </div>

              {hintData && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-amber-300 flex items-center gap-1.5">
                    <Lightbulb className="w-4 h-4 text-amber-400" />
                    <span>Progressive Socratic Hint (Level {hintData.level}):</span>
                  </div>
                  <p className="text-xs text-slate-200 leading-relaxed bg-amber-500/10 p-3 rounded-xl border border-amber-500/20 font-medium">
                    {hintData.hint}
                  </p>
                  {hintData.pedagogical_guidance && (
                    <div className="text-[11px] text-slate-400 italic">
                      Guidance: {hintData.pedagogical_guidance}
                    </div>
                  )}
                </div>
              )}

              {explanationData && (
                <div className="space-y-3 pt-2 border-t border-white/[0.08]">
                  <div className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                    <BookOpen className="w-4 h-4 text-indigo-400" />
                    <span>Conceptual Breakdown &amp; Model Solution:</span>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed bg-indigo-500/10 p-3 rounded-xl border border-indigo-500/20">
                    {explanationData.model_answer}
                  </p>

                  {explanationData.key_takeaways?.length > 0 && (
                    <div className="space-y-1">
                      <div className="text-[11px] font-mono font-bold text-cyan-300">Key Takeaways:</div>
                      <ul className="list-disc list-inside text-xs text-slate-300 space-y-0.5">
                        {explanationData.key_takeaways.map((t, idx) => (
                          <li key={idx}>{t}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Real-time Delivery Acoustics Meter */}
          <EmotionMeter
            silenceRatio={audioMetrics.silenceRatio}
            pitchVarianceScore={audioMetrics.pitchVarianceScore}
            fillerWordRate={audioMetrics.fillerWordRate}
            speechRateWpm={audioMetrics.speechRateWpm}
          />

          {/* Live Whisper Transcript Display */}
          {partialTranscript && (
            <div className="p-4 rounded-2xl border border-cyan-500/30 bg-cyan-500/5">
              <span className="text-[10px] uppercase font-bold text-cyan-400 tracking-wider block mb-1 font-mono">
                Live Speech Stream
              </span>
              <p className="text-sm text-slate-200 leading-relaxed font-mono">
                {partialTranscript}
              </p>
            </div>
          )}

          {/* Answer Mode Toggle: Mic or Typed Code/Text */}
          <div className="p-6 rounded-3xl border border-white/10 bg-slate-900/60 flex flex-col items-center justify-center gap-4">
            <div className="flex items-center gap-2 text-xs font-mono">
              <button
                type="button"
                onClick={() => setTextAnswerMode(false)}
                className={`px-3 py-1 rounded-xl transition-all cursor-pointer ${
                  !textAnswerMode
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                🎙️ Speak Aloud (Voice)
              </button>
              <button
                type="button"
                onClick={() => setTextAnswerMode(true)}
                className={`px-3 py-1 rounded-xl transition-all cursor-pointer ${
                  textAnswerMode
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                ⌨️ Type / Write Solution
              </button>
            </div>

            {textAnswerMode ? (
              <div className="w-full space-y-3">
                <textarea
                  value={typedAnswer}
                  onChange={(e) => setTypedAnswer(e.target.value)}
                  placeholder="Type your structured explanation, code snippet, or architectural trade-offs here..."
                  rows={4}
                  className="w-full p-3.5 rounded-2xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 font-mono"
                />
                <div className="flex justify-end">
                  <button
                    type="button"
                    onClick={handleSubmitTextAnswer}
                    disabled={!typedAnswer.trim() || isSubmittingText}
                    className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer shadow-md"
                  >
                    <span>{isSubmittingText ? 'Evaluating...' : 'Submit Answer'}</span>
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ) : isProcessing ? (
              <div className="flex flex-col items-center gap-3">
                <div className="flex gap-1 items-end h-8">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="w-1.5 h-6 bg-cyan-400 rounded-full animate-bounce"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <p className="text-xs text-cyan-300 font-medium animate-pulse font-mono">
                  Evaluating semantic depth, trade-offs &amp; rubric scoring...
                </p>
              </div>
            ) : isRecording ? (
              <div className="flex flex-col items-center gap-3">
                <button
                  id="stop-recording-btn"
                  onClick={handleStopRecording}
                  className="w-16 h-16 rounded-full bg-rose-500 hover:bg-rose-600 flex items-center justify-center transition-all shadow-xl shadow-rose-500/30 cursor-pointer"
                >
                  <span className="w-5 h-5 rounded-sm bg-white" />
                </button>
                <div className="flex items-center gap-2 text-rose-400 text-xs font-bold tracking-wider uppercase font-mono">
                  <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />
                  Recording {String(Math.floor(recordingTime / 60)).padStart(2, '0')}:
                  {String(recordingTime % 60).padStart(2, '0')}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <button
                  id="start-recording-btn"
                  onClick={handleStartRecording}
                  disabled={!connected || !currentQuestion || isPaused}
                  className="w-16 h-16 rounded-full bg-cyan-500 hover:bg-cyan-400 flex items-center justify-center transition-all shadow-xl shadow-cyan-500/30 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <Mic className="w-6 h-6 text-slate-950" />
                </button>
                <p className="text-xs text-slate-400 font-mono">
                  Click microphone to answer aloud
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Informed Consent & Device Permission Modal */}
      {showConsentModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-fade-in">
          <div className="w-full max-w-lg p-6 sm:p-8 rounded-3xl bg-slate-900 border border-slate-800 shadow-2xl space-y-6">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-2xl bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center text-cyan-400 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-lg font-extrabold text-white">Pre-Interview Consent &amp; Recording Setup</h3>
                <p className="text-xs text-slate-400">Choose your recording preferences for this session.</p>
              </div>
            </div>

            <div className="space-y-3">
              <label
                onClick={() => setConsentChoice('video_audio')}
                className={`p-4 rounded-2xl border flex items-start gap-3 cursor-pointer transition-all ${
                  consentChoice === 'video_audio'
                    ? 'bg-cyan-500/10 border-cyan-400 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="consent"
                  checked={consentChoice === 'video_audio'}
                  onChange={() => setConsentChoice('video_audio')}
                  className="mt-1 accent-cyan-400"
                />
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Video className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Full Video &amp; Audio Recording (Recommended)</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Enables eye-contact tracking, composure metrics, and full session video playback in your report.
                  </div>
                </div>
              </label>

              <label
                onClick={() => setConsentChoice('audio_only')}
                className={`p-4 rounded-2xl border flex items-start gap-3 cursor-pointer transition-all ${
                  consentChoice === 'audio_only'
                    ? 'bg-cyan-500/10 border-cyan-400 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="consent"
                  checked={consentChoice === 'audio_only'}
                  onChange={() => setConsentChoice('audio_only')}
                  className="mt-1 accent-cyan-400"
                />
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <Mic className="w-3.5 h-3.5 text-indigo-400" />
                    <span>Audio Only Recording</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Record voice acoustics, speech rate, and WPM without enabling the camera.
                  </div>
                </div>
              </label>

              <label
                onClick={() => setConsentChoice('no_recording')}
                className={`p-4 rounded-2xl border flex items-start gap-3 cursor-pointer transition-all ${
                  consentChoice === 'no_recording'
                    ? 'bg-cyan-500/10 border-cyan-400 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400'
                }`}
              >
                <input
                  type="radio"
                  name="consent"
                  checked={consentChoice === 'no_recording'}
                  onChange={() => setConsentChoice('no_recording')}
                  className="mt-1 accent-cyan-400"
                />
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                    <VideoOff className="w-3.5 h-3.5 text-slate-400" />
                    <span>No Recording (Private Practice)</span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    Only text transcripts and AI evaluations are analyzed. No media stored.
                  </div>
                </div>
              </label>
            </div>

            <div className="p-3.5 rounded-xl bg-white/[0.03] border border-white/[0.06] text-[11px] text-slate-400 leading-relaxed">
              🔒 <strong>Privacy Assurance:</strong> Recordings are encrypted and stored in private cloud storage. You can permanently delete all video files anytime from your report page.
            </div>

            <button
              type="button"
              onClick={handleConfirmConsent}
              className="w-full py-3.5 rounded-2xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs uppercase tracking-wider transition-all cursor-pointer shadow-lg"
            >
              Confirm &amp; Enter Interview Arena
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
