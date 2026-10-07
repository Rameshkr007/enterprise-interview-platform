import { create } from 'zustand'
import type { AudioMetrics, InterviewSession, QuestionPayload, WsMessage } from '@/lib/types'

interface InterviewStore {
  session: InterviewSession | null
  currentQuestion: QuestionPayload | null
  partialTranscript: string
  turnAudioMetrics: AudioMetrics | null
  isRecording: boolean
  isProcessing: boolean
  isComplete: boolean
  allScores: number[]

  setSession: (s: InterviewSession) => void
  setCurrentQuestion: (q: QuestionPayload) => void
  appendPartial: (text: string) => void
  clearPartial: () => void
  setRecording: (v: boolean) => void
  setProcessing: (v: boolean) => void
  handleWsMessage: (msg: WsMessage) => void
  reset: () => void
}

const DEFAULT = {
  session: null,
  currentQuestion: null,
  partialTranscript: '',
  turnAudioMetrics: null,
  isRecording: false,
  isProcessing: false,
  isComplete: false,
  allScores: [],
}

export const useInterviewStore = create<InterviewStore>((set) => ({
  ...DEFAULT,

  setSession: (session) => set({ session }),
  setCurrentQuestion: (currentQuestion) => set({ currentQuestion }),
  appendPartial: (text) => set((s) => ({ partialTranscript: s.partialTranscript + ' ' + text })),
  clearPartial: () => set({ partialTranscript: '' }),
  setRecording: (isRecording) => set({ isRecording }),
  setProcessing: (isProcessing) => set({ isProcessing }),

  handleWsMessage: (msg) => {
    switch (msg.type) {
      case 'partial_transcript':
        set((s) => ({ partialTranscript: s.partialTranscript + ' ' + (msg.payload.text as string) }))
        break
      case 'question':
        set({
          currentQuestion: msg.payload as unknown as QuestionPayload,
          partialTranscript: '',
          isProcessing: false,
          turnAudioMetrics: (msg.payload.audio_metrics as AudioMetrics) ?? null,
        })
        break
      case 'complete':
        set({
          isComplete: true,
          isProcessing: false,
          allScores: (msg.payload.all_scores as number[]) ?? [],
        })
        break
      case 'error':
        set({ isProcessing: false })
        break
    }
  },

  reset: () => set(DEFAULT),
}))
