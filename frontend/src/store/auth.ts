import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { User } from '@/lib/types'
import { authApi } from '@/lib/api'

interface AuthState {
  user: User | null
  access_token: string | null
  refresh_token: string | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  fetchMe: () => Promise<void>
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      access_token: null,
      refresh_token: null,
      isLoading: false,

      login: async (email, password) => {
        set({ isLoading: true })
        try {
          const tokens = await authApi.login({ email, password })
          localStorage.setItem('access_token', tokens.access_token)
          localStorage.setItem('refresh_token', tokens.refresh_token)
          const user = await authApi.me()
          set({
            user,
            access_token: tokens.access_token,
            refresh_token: tokens.refresh_token,
            isLoading: false,
          })
        } catch (err) {
          set({ isLoading: false })
          throw err
        }
      },

      logout: async () => {
        const rt = get().refresh_token || (typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null)
        try {
          if (rt) {
            await authApi.logout(rt)
          }
        } catch {
          // Ignore network errors on logout
        } finally {
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
          }
          set({ user: null, access_token: null, refresh_token: null })
        }
      },

      fetchMe: async () => {
        try {
          const user = await authApi.me()
          set({ user })
        } catch {
          set({ user: null })
        }
      },
    }),
    {
      name: 'auth-store',
      partialize: (s) => ({ access_token: s.access_token, refresh_token: s.refresh_token, user: s.user }),
    }
  )
)
