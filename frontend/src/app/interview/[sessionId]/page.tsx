'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useInterviewStore } from '@/store/interview'
import { useWebSocket } from '@/hooks/useWebSocket'
import { useAudioCapture } from '@/hooks/useAudioCapture'
import { useAuthStore } from '@/store/auth'
import type { WsMessage } from '@/lib/types'

import { AIInterviewerAvatar } from '@/components/interview/AIInterviewerAvatar'
import { WebcamEmotionTracker } from '@/components/interview/WebcamEmotionTracker'
import { TTSPlayer } from '@/components/interview/TTSPlayer'
import { EmotionMeter } from '@/components/interview/EmotionMeter'
import { CoachWhisper } from '@/components/interview/CoachWhisper'

function DifficultyBadge({ difficulty }: { difficulty: string }) {
  const map: Record<string, string> = {
    easy: 'badge badge-success',
    medium: 'badge badge-info',
    hard: 'badge badge-warning',
    expert: 'badge badge-danger',
  }
  return <span className={map[difficulty] ?? 'badge badge-info'}>{difficulty}</span>
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

  // Audio metrics for delivery meter
  const [audioMetrics, setAudioMetrics] = useState({
    silenceRatio: 0.12,
    pitchVarianceScore: 0.65,
    fillerWordRate: 1.2,
    speechRateWpm: 135,
  })

  const onWsMessage = useCallback(
    (msg: WsMessage) => {
      handleWsMessage(msg)
      if (msg.type === 'error') {
        setWsError(msg.payload.message as string)
      } else if (msg.type === 'question') {
        setIsAiSpeaking(true)
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
    [handleWsMessage]
  )

  const { status, connect, sendAudioChunk, sendAudioEnd } = useWebSocket(onWsMessage)
  const { startRecording, stopRecording, error: audioError } = useAudioCapture()

  useEffect(() => {
    if (access_token && sessionId) {
      connect(sessionId, access_token)
      setConnected(true)
    }
    return () => reset()
  }, [access_token, sessionId, connect, reset])

  useEffect(() => {
    if (status === 'connected') setConnected(true)
    if (status === 'error') setWsError('WebSocket connection failed')
  }, [status])

  async function handleStartRecording() {
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

  if (isComplete) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center gap-8 animate-fade-in px-6">
        <div className="text-6xl mb-4">🎉</div>
        <h1 className="text-3xl font-bold text-white text-center">Interview Complete!</h1>
        <p className="text-slate-400 text-center max-w-md">
          Your responses, acoustic features, and vision metrics have been compiled. View your multi-dimensional report.
        </p>
        <div className="flex gap-4">
          <button
            id="view-report-btn"
            onClick={() => router.push(`/report/${sessionId}`)}
            className="btn-primary px-8 py-3"
          >
            View Full Report
          </button>
          <button onClick={() => router.push('/dashboard')} className="btn-ghost px-8 py-3">
            Dashboard
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col max-w-7xl mx-auto px-4 sm:px-6 py-6 animate-fade-in space-y-6">
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
          <span className="text-slate-300 font-medium text-sm">
            {connected ? 'Live AI Interview Session' : 'Connecting to Gateway...'}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {currentQuestion && (
            <DifficultyBadge difficulty={currentQuestion.difficulty} />
          )}
          <button
            onClick={() => router.push('/dashboard')}
            className="btn-ghost text-xs py-1.5 px-3"
          >
            Exit Session
          </button>
        </div>
      </div>

      {/* Error Alert */}
      {(wsError || audioError) && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
          {wsError || audioError}
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

        {/* Right Side: Active Question, Voice Synthesis & Recording Area */}
        <div className="lg:col-span-7 flex flex-col gap-5">
          {/* Question Presentation Card */}
          <div className="glass-card p-6 sm:p-8 rounded-2xl border border-white/10 bg-slate-900/60 shadow-xl space-y-4">
            <div className="flex items-center justify-between">
              <span className="badge badge-info capitalize">
                {currentQuestion?.category || 'Technical Assessment'}
              </span>
              <span className="text-slate-400 text-xs font-semibold">
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
          </div>

          {/* Real-time Delivery Acoustics Meter */}
          <EmotionMeter
            silenceRatio={audioMetrics.silenceRatio}
            pitchVarianceScore={audioMetrics.pitchVarianceScore}
            fillerWordRate={audioMetrics.fillerWordRate}
            speechRateWpm={audioMetrics.speechRateWpm}
          />

          {/* Live Whisper Transcript Display */}
          {partialTranscript && (
            <div className="glass-card p-4 rounded-xl border border-brand-500/30 bg-brand-500/5">
              <span className="text-[10px] uppercase font-bold text-brand-400 tracking-wider block mb-1">
                Live Speech Stream
              </span>
              <p className="text-sm text-slate-200 leading-relaxed font-mono">
                {partialTranscript}
              </p>
            </div>
          )}

          {/* Answer Recording Action Controller */}
          <div className="glass-card p-6 rounded-2xl border border-white/10 bg-slate-900/60 flex flex-col items-center justify-center gap-4">
            {isProcessing ? (
              <div className="flex flex-col items-center gap-3">
                <div className="flex gap-1 items-end h-8">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className="waveform-bar"
                      style={{ animationDelay: `${i * 0.15}s` }}
                    />
                  ))}
                </div>
                <p className="text-xs text-brand-300 font-medium animate-pulse">
                  Extracting acoustic features & evaluating semantic depth...
                </p>
              </div>
            ) : isRecording ? (
              <div className="flex flex-col items-center gap-3">
                <div className="recording-indicator">
                  <button
                    id="stop-recording-btn"
                    onClick={handleStopRecording}
                    className="w-16 h-16 rounded-full bg-rose-500 hover:bg-rose-600 flex items-center justify-center transition-all shadow-xl shadow-rose-500/30 cursor-pointer"
                  >
                    <span className="w-5 h-5 rounded-sm bg-white" />
                  </button>
                </div>
                <div className="flex items-center gap-2 text-rose-400 text-xs font-bold tracking-wider uppercase">
                  <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />
                  Recording{' '}
                  {String(Math.floor(recordingTime / 60)).padStart(2, '0')}:
                  {String(recordingTime % 60).padStart(2, '0')}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <button
                  id="start-recording-btn"
                  onClick={handleStartRecording}
                  disabled={!connected || !currentQuestion}
                  className="w-16 h-16 rounded-full bg-brand-500 hover:bg-brand-600 flex items-center justify-center transition-all shadow-xl shadow-brand-500/30 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
                >
                  <svg
                    className="w-6 h-6 text-white"
                    fill="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path d="M12 15a3 3 0 003-3V6a3 3 0 00-6 0v6a3 3 0 003 3z" />
                    <path d="M5 11a7 7 0 0014 0h-2a5 5 0 01-10 0H5z" />
                    <path d="M11 19v2h2v-2h1a8 8 0 001-15.93V3h-6v.07A8 8 0 0011 19z" />
                  </svg>
                </button>
                <p className="text-xs text-slate-400">
                  Click microphone to answer aloud
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
