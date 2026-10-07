'use client'
import { useCallback, useRef, useState } from 'react'

const SAMPLE_RATE = 16_000
const CHUNK_INTERVAL_MS = 250

export interface UseAudioCaptureReturn {
  isRecording: boolean
  startRecording: (onChunk: (chunk: ArrayBuffer) => void) => Promise<void>
  stopRecording: () => Promise<ArrayBuffer>
  error: string | null
}

export function useAudioCapture(): UseAudioCaptureReturn {
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<ArrayBuffer[]>([])
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const resolveRef = useRef<((buf: ArrayBuffer) => void) | null>(null)

  const startRecording = useCallback(async (onChunk: (chunk: ArrayBuffer) => void) => {
    setError(null)
    chunksRef.current = []
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })
      streamRef.current = stream

      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' })
      mediaRecorderRef.current = recorder

      recorder.ondataavailable = async (e) => {
        if (e.data.size > 0) {
          const buf = await e.data.arrayBuffer()
          chunksRef.current.push(buf)
          onChunk(buf)
        }
      }

      recorder.start(CHUNK_INTERVAL_MS)
      setIsRecording(true)
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Microphone access denied'
      setError(msg)
      throw new Error(msg)
    }
  }, [])

  const stopRecording = useCallback((): Promise<ArrayBuffer> => {
    return new Promise((resolve) => {
      resolveRef.current = resolve
      const recorder = mediaRecorderRef.current
      if (!recorder || recorder.state === 'inactive') {
        resolve(new ArrayBuffer(0))
        return
      }
      recorder.onstop = () => {
        streamRef.current?.getTracks().forEach((t) => t.stop())
        setIsRecording(false)
        // Combine all chunks
        const total = chunksRef.current.reduce((acc, b) => acc + b.byteLength, 0)
        const combined = new Uint8Array(total)
        let offset = 0
        for (const chunk of chunksRef.current) {
          combined.set(new Uint8Array(chunk), offset)
          offset += chunk.byteLength
        }
        resolve(combined.buffer)
      }
      recorder.stop()
    })
  }, [])

  return { isRecording, startRecording, stopRecording, error }
}
