import { useEffect, useState } from 'react'
import { MagnifyingGlassIcon, FunnelIcon } from '@heroicons/react/24/outline'
import { getCalls } from '../api/callsApi'
import CallTable from '../components/calls/CallTable'
import CallDetailModal from '../components/calls/CallDetailModal'
import Spinner from '../components/ui/Spinner'

const OUTCOMES = ['', 'booked', 'missed', 'faq', 'transferred', 'cancelled', 'unknown']
const DIRECTIONS = ['', 'inbound', 'outbound']

export default function CallLogs() {
  const [calls, setCalls] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedId, setSelectedId] = useState(null)
  const [filters, setFilters] = useState({ search: '', outcome: '', direction: '', date_from: '', date_to: '' })
  const [page, setPage] = useState(1)
  const [count, setCount] = useState(0)

  const fetchCalls = () => {
    setLoading(true)
    const params = { page, ...Object.fromEntries(Object.entries(filters).filter(([, v]) => v)) }
    getCalls(params)
      .then(({ data }) => { setCalls(data.results ?? data); setCount(data.count ?? (data.results ?? data).length) })
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetchCalls() }, [page, filters])

  const setFilter = (key, val) => { setPage(1); setFilters((f) => ({ ...f, [key]: val })) }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-white">Call Logs</h1>

      {/* Filter bar */}
      <div className="card flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-48">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            className="input pl-9"
            placeholder="Search caller, summary…"
            value={filters.search}
            onChange={(e) => setFilter('search', e.target.value)}
          />
        </div>
        <select className="input w-36" value={filters.outcome} onChange={(e) => setFilter('outcome', e.target.value)}>
          {OUTCOMES.map((o) => <option key={o} value={o}>{o || 'All outcomes'}</option>)}
        </select>
        <select className="input w-36" value={filters.direction} onChange={(e) => setFilter('direction', e.target.value)}>
          {DIRECTIONS.map((d) => <option key={d} value={d}>{d || 'All directions'}</option>)}
        </select>
        <input type="date" className="input w-36" value={filters.date_from} onChange={(e) => setFilter('date_from', e.target.value)} />
        <input type="date" className="input w-36" value={filters.date_to} onChange={(e) => setFilter('date_to', e.target.value)} />
        {Object.values(filters).some(Boolean) && (
          <button className="btn-ghost text-xs" onClick={() => { setFilters({ search: '', outcome: '', direction: '', date_from: '', date_to: '' }); setPage(1) }}>
            Clear
          </button>
        )}
        <span className="text-xs text-gray-500 ml-auto">{count} calls</span>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16"><Spinner /></div>
        ) : (
          <CallTable calls={calls} onSelect={setSelectedId} />
        )}
      </div>

      {/* Pagination */}
      {count > 25 && (
        <div className="flex justify-center gap-2">
          <button disabled={page === 1} className="btn-ghost text-xs" onClick={() => setPage(p => p - 1)}>← Prev</button>
          <span className="text-xs text-gray-500 self-center">Page {page}</span>
          <button disabled={calls.length < 25} className="btn-ghost text-xs" onClick={() => setPage(p => p + 1)}>Next →</button>
        </div>
      )}

      <CallDetailModal callId={selectedId} onClose={() => setSelectedId(null)} />
    </div>
  )
}
