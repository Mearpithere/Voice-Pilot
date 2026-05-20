import { useEffect, useRef, useState } from 'react'
import { PlayIcon, PauseIcon, ArrowDownTrayIcon } from '@heroicons/react/24/solid'
import { getCallRecording } from '../../api/callsApi'
import Spinner from '../ui/Spinner'

export default function AudioPlayer({ callId, hasRecording }) {
  const [url, setUrl] = useState(null)
  const [loading, setLoading] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [progress, setProgress] = useState(0)
  const [duration, setDuration] = useState(0)
  const audioRef = useRef(null)

  useEffect(() => {
    if (!hasRecording || !callId) return
    setLoading(true)
    getCallRecording(callId)
      .then(({ data }) => setUrl(data.url))
      .finally(() => setLoading(false))
  }, [callId, hasRecording])

  const toggle = () => {
    if (!audioRef.current) return
    if (playing) { audioRef.current.pause() } else { audioRef.current.play() }
    setPlaying(!playing)
  }

  const onTimeUpdate = () => {
    if (!audioRef.current) return
    setProgress((audioRef.current.currentTime / audioRef.current.duration) * 100 || 0)
  }

  const onSeek = (e) => {
    if (!audioRef.current) return
    const pct = e.nativeEvent.offsetX / e.currentTarget.offsetWidth
    audioRef.current.currentTime = pct * audioRef.current.duration
  }

  const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`

  if (!hasRecording) {
    return <p className="text-sm text-gray-500 italic">No recording available.</p>
  }
  if (loading) return <div className="flex items-center gap-2 text-sm text-gray-400"><Spinner size="sm" /> Loading recording…</div>
  if (!url) return <p className="text-sm text-red-400">Could not load recording.</p>

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <audio
        ref={audioRef}
        src={url}
        onTimeUpdate={onTimeUpdate}
        onLoadedMetadata={() => setDuration(audioRef.current?.duration || 0)}
        onEnded={() => setPlaying(false)}
        className="hidden"
      />
      <div className="flex items-center gap-3">
        <button onClick={toggle} className="w-9 h-9 rounded-full bg-brand-600 hover:bg-brand-700 flex items-center justify-center shrink-0 transition-colors">
          {playing
            ? <PauseIcon className="w-4 h-4 text-white" />
            : <PlayIcon className="w-4 h-4 text-white ml-0.5" />}
        </button>
        <div className="flex-1">
          <div className="h-1.5 bg-gray-700 rounded-full cursor-pointer" onClick={onSeek}>
            <div className="h-full bg-brand-500 rounded-full transition-all" style={{ width: `${progress}%` }} />
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>{fmt(audioRef.current?.currentTime || 0)}</span>
            <span>{fmt(duration)}</span>
          </div>
        </div>
        <a href={url} download className="text-gray-500 hover:text-white transition-colors">
          <ArrowDownTrayIcon className="w-4 h-4" />
        </a>
      </div>
    </div>
  )
}
