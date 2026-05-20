import { useEffect, useState } from 'react'
import { getAppointments } from '../api/appointmentsApi'
import AppointmentTable from '../components/appointments/AppointmentTable'
import Spinner from '../components/ui/Spinner'

const STATUSES = ['', 'scheduled', 'confirmed', 'cancelled', 'no_show', 'completed']

export default function Appointments() {
  const [appointments, setAppointments] = useState([])
  const [loading, setLoading] = useState(true)
  const [filters, setFilters] = useState({ status: '', date_from: '', date_to: '' })

  const fetch = () => {
    setLoading(true)
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    getAppointments(params)
      .then(({ data }) => setAppointments(data.results ?? data))
      .finally(() => setLoading(false))
  }

  useEffect(() => { fetch() }, [filters])

  const setFilter = (k, v) => setFilters((f) => ({ ...f, [k]: v }))

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-xl font-bold text-white">Appointments</h1>

      <div className="card flex flex-wrap gap-3 items-center">
        <select className="input w-40" value={filters.status} onChange={(e) => setFilter('status', e.target.value)}>
          {STATUSES.map((s) => <option key={s} value={s}>{s || 'All statuses'}</option>)}
        </select>
        <input type="date" className="input w-36" value={filters.date_from} onChange={(e) => setFilter('date_from', e.target.value)} />
        <input type="date" className="input w-36" value={filters.date_to} onChange={(e) => setFilter('date_to', e.target.value)} />
        {Object.values(filters).some(Boolean) && (
          <button className="btn-ghost text-xs" onClick={() => setFilters({ status: '', date_from: '', date_to: '' })}>Clear</button>
        )}
        <span className="text-xs text-gray-500 ml-auto">{appointments.length} appointments</span>
      </div>

      <div className="card p-0 overflow-hidden">
        {loading ? <div className="flex justify-center py-16"><Spinner /></div>
          : <AppointmentTable appointments={appointments} onRefresh={fetch} />}
      </div>
    </div>
  )
}
