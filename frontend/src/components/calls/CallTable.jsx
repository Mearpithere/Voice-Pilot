import { format } from 'date-fns'
import Badge from '../ui/Badge'
import { PhoneArrowDownLeftIcon, PhoneArrowUpRightIcon } from '@heroicons/react/24/outline'

export default function CallTable({ calls, onSelect }) {
  if (!calls?.length) {
    return (
      <div className="text-center py-16 text-gray-500">
        <PhoneArrowDownLeftIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-sm">No calls found.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
            <th className="text-left px-4 py-3 font-medium">Caller</th>
            <th className="text-left px-4 py-3 font-medium">Direction</th>
            <th className="text-left px-4 py-3 font-medium">Outcome</th>
            <th className="text-left px-4 py-3 font-medium">Duration</th>
            <th className="text-left px-4 py-3 font-medium">Time</th>
          </tr>
        </thead>
        <tbody>
          {calls.map((call) => (
            <tr key={call.id} className="table-row" onClick={() => onSelect(call.id)}>
              <td className="px-4 py-3">
                <p className="font-medium text-white">{call.caller_name || call.caller_number}</p>
                {call.caller_name && <p className="text-xs text-gray-500">{call.caller_number}</p>}
              </td>
              <td className="px-4 py-3">
                <span className="flex items-center gap-1.5 text-gray-400">
                  {call.direction === 'inbound'
                    ? <PhoneArrowDownLeftIcon className="w-3.5 h-3.5 text-indigo-400" />
                    : <PhoneArrowUpRightIcon className="w-3.5 h-3.5 text-purple-400" />}
                  {call.direction}
                </span>
              </td>
              <td className="px-4 py-3">
                <Badge value={call.outcome} label={call.outcome_display} />
              </td>
              <td className="px-4 py-3 text-gray-400">
                {call.duration_minutes != null ? `${call.duration_minutes} min` : '—'}
              </td>
              <td className="px-4 py-3 text-gray-500 text-xs">
                {call.started_at ? format(new Date(call.started_at), 'dd MMM, h:mm a') : '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
