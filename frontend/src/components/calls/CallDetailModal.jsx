import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { getCall } from '../../api/callsApi'
import Modal from '../ui/Modal'
import Badge from '../ui/Badge'
import AudioPlayer from './AudioPlayer'
import TranscriptViewer from './TranscriptViewer'
import Spinner from '../ui/Spinner'

export default function CallDetailModal({ callId, onClose }) {
  const [call, setCall] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!callId) return
    setLoading(true)
    getCall(callId)
      .then(({ data }) => setCall(data))
      .finally(() => setLoading(false))
  }, [callId])

  return (
    <Modal open={!!callId} onClose={onClose} title="Call Details" wide>
      {loading && <div className="flex justify-center py-10"><Spinner /></div>}
      {!loading && call && (
        <div className="space-y-5">
          {/* Header row */}
          <div className="flex items-start justify-between flex-wrap gap-3">
            <div>
              <p className="text-lg font-semibold text-white">{call.caller_name || call.caller_number}</p>
              {call.caller_name && <p className="text-sm text-gray-400">{call.caller_number}</p>}
              <p className="text-xs text-gray-500 mt-1">
                {call.started_at ? format(new Date(call.started_at), 'PPpp') : '—'}
              </p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Badge value={call.direction} label={call.direction === 'inbound' ? 'Inbound' : 'Outbound'} />
              <Badge value={call.outcome} label={call.outcome_display} />
            </div>
          </div>

          {/* Stats row */}
          <div className="grid grid-cols-3 gap-3">
            {[
              ['Duration', call.duration_seconds ? `${call.duration_minutes} min` : '—'],
              ['CRM Synced', call.crm_synced ? 'Yes' : 'No'],
              ['Status', call.status],
            ].map(([label, val]) => (
              <div key={label} className="bg-gray-800 rounded-lg p-3 text-center">
                <p className="text-xs text-gray-500">{label}</p>
                <p className="text-sm font-medium text-white mt-0.5">{val}</p>
              </div>
            ))}
          </div>

          {/* Summary */}
          {call.summary && (
            <div>
              <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Summary</h3>
              <p className="text-sm text-gray-300 bg-gray-800 rounded-lg p-3 leading-relaxed">{call.summary}</p>
            </div>
          )}

          {/* Recording */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Recording</h3>
            <AudioPlayer callId={call.id} hasRecording={!!call.recording_url} />
          </div>

          {/* Transcript */}
          <div>
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">Transcript</h3>
            <TranscriptViewer transcript={call.transcript} />
          </div>
        </div>
      )}
    </Modal>
  )
}
