'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsMessage } from '@/lib/types'

export function getWsBase(): string {
  if (process.env.NEXT_PUBLIC_WS_URL) {
    return process.env.NEXT_PUBLIC_WS_URL
  }
  if (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    return 'wss://enterprise-interview-platform.onrender.com'
  }
  return 'ws://localhost:8000'
}

const WS_BASE = getWsBase()

export type WsStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export interface UseWebSocketReturn {
  status: WsStatus
  connect: (sessionId: string, token: string) => void
  disconnect: () => void
  sendAudioChunk: (chunk: ArrayBuffer) => void
  sendAudioEnd: () => void
  lastMessage: WsMessage | null
}

export function useWebSocket(
  onMessage: (msg: WsMessage) => void
): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null)
  const [status, setStatus] = useState<WsStatus>('disconnected')
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)

  const connect = useCallback(
    (sessionId: string, token: string) => {
      // Pick freshest token from localStorage if available
      const storedToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
      const rawToken = storedToken || token
      if (!rawToken || rawToken === 'null' || rawToken === 'undefined') {
        setStatus('error')
        return
      }

      // Close previous connection if active before re-connecting
      if (wsRef.current) {
        try {
          wsRef.current.close()
        } catch {}
        wsRef.current = null
      }

      setStatus('connecting')
      const cleanToken = rawToken.replace(/^Bearer\s+/i, '').trim().replace(/^["']|["']$/g, '')
      const url = `${getWsBase()}/ws/interview/${sessionId}?token=${encodeURIComponent(cleanToken)}`
      const ws = new WebSocket(url)
      ws.binaryType = 'arraybuffer'

      ws.onopen = () => setStatus('connected')

      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data as string)
          setLastMessage(msg)
          onMessage(msg)
        } catch {
          // binary ack - ignore
        }
      }

      ws.onerror = () => setStatus('error')

      ws.onclose = () => {
        setStatus('disconnected')
        wsRef.current = null
      }

      wsRef.current = ws
    },
    [onMessage]
  )

  const disconnect = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  const sendAudioChunk = useCallback((chunk: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(chunk)
    }
  }, [])

  const sendAudioEnd = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'audio_end' }))
    }
  }, [])

  useEffect(() => () => disconnect(), [disconnect])

  return { status, connect, disconnect, sendAudioChunk, sendAudioEnd, lastMessage }
}
