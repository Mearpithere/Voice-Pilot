import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import api from '../api/axios'

const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      user: null,
      clinic: null,

      login: async (username, password) => {
        const { data } = await api.post('/api/auth/login/', { username, password })
        set({ token: data.token, user: data.user, clinic: data.clinic })
        return data
      },

      logout: async () => {
        try { await api.post('/api/auth/logout/') } catch (_) {}
        set({ token: null, user: null, clinic: null })
      },

      updateClinic: (clinic) => set({ clinic }),
    }),
    { name: 'voicepilot-auth' }
  )
)

export default useAuthStore
