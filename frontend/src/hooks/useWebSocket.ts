'use client'
import { useCallback, useEffect, useRef, useState } from 'react'
import type { WsMessage } from '@/lib/types'

const WS_BASE = process.env.NEXT_PUBLIC_WS_URL ?? 'ws://localhost:8000'

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
      if (wsRef.current?.readyState === WebSocket.OPEN) return

      setStatus('connecting')
      const url = `${WS_BASE}/ws/interview/${sessionId}?token=${encodeURIComponent(token)}`
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
