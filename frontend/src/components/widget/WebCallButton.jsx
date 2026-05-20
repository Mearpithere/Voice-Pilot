import { useState, useCallback } from 'react'
import { PhoneIcon, XMarkIcon } from '@heroicons/react/24/solid'
import { getWebCallToken } from '../../api/clinicsApi'
import useAuthStore from '../../store/authStore'
import clsx from 'clsx'

export default function WebCallButton({ preview = false }) {
  const [status, setStatus] = useState('idle') // idle | connecting | active | error
  const [room, setRoom] = useState(null)
  const clinic = useAuthStore((s) => s.clinic)

  const startCall = useCallback(async () => {
    if (!clinic?.id) return
    setStatus('connecting')
    try {
      const { data } = await getWebCallToken(clinic.id)
      // Dynamically import to keep bundle small
      const { Room, RoomEvent } = await import('livekit-client')
      const lkRoom = new Room()
      lkRoom.on(RoomEvent.Disconnected, () => setStatus('idle'))
      await lkRoom.connect(import.meta.env.VITE_LIVEKIT_URL, data.token, {
        audio: true,
        video: false,
      })
      setRoom(lkRoom)
      setStatus('active')
    } catch (e) {
      console.error(e)
      setStatus('error')
      setTimeout(() => setStatus('idle'), 3000)
    }
  }, [clinic])

  const endCall = useCallback(async () => {
    await room?.disconnect()
    setRoom(null)
    setStatus('idle')
  }, [room])

  const labels = {
    idle: 'Start Call',
    connecting: 'Connecting…',
    active: 'End Call',
    error: 'Failed — retry?',
  }

  return (
    <div className={clsx('flex flex-col items-center gap-3', preview && 'pointer-events-none')}>
      <button
        onClick={status === 'active' ? endCall : startCall}
        disabled={status === 'connecting'}
        className={clsx(
          'w-16 h-16 rounded-full flex items-center justify-center shadow-lg transition-all',
          status === 'active'
            ? 'bg-red-600 hover:bg-red-700 animate-pulse'
            : status === 'error'
            ? 'bg-orange-600'
            : 'bg-brand-600 hover:bg-brand-700',
          status === 'connecting' && 'opacity-70 cursor-not-allowed'
        )}
      >
        {status === 'active'
          ? <XMarkIcon className="w-7 h-7 text-white" />
          : <PhoneIcon className="w-7 h-7 text-white" />}
      </button>
      <span className="text-sm text-gray-400">{labels[status]}</span>
    </div>
  )
}
