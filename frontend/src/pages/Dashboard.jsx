import { useEffect, useState } from 'react'
import {
  PhoneIcon, CalendarDaysIcon, PhoneXMarkIcon, ClockIcon,
} from '@heroicons/react/24/outline'
import { getCallStats } from '../api/callsApi'
import { getTodayAppointments } from '../api/appointmentsApi'
import StatsCard from '../components/ui/StatsCard'
import AppointmentTable from '../components/appointments/AppointmentTable'
import useAuthStore from '../store/authStore'
import { format } from 'date-fns'

export default function Dashboard() {
  const clinic = useAuthStore((s) => s.clinic)
  const [stats, setStats] = useState(null)
  const [appointments, setAppointments] = useState([])
  const [period, setPeriod] = useState('today')

  const fetchStats = () =>
    getCallStats(period).then(({ data }) => setStats(data))

  const fetchAppts = () =>
    getTodayAppointments().then(({ data }) => setAppointments(data))

  useEffect(() => { fetchStats() }, [period])
  useEffect(() => { fetchAppts() }, [])

  return (
    <div className="p-6 space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">{clinic?.name || 'Dashboard'}</h1>
          <p className="text-sm text-gray-400">{format(new Date(), 'EEEE, MMMM d')}</p>
        </div>
        <div className="flex gap-1 bg-gray-800 rounded-lg p-1">
          {['today', 'week', 'month'].map((p) => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 text-xs font-medium rounded-md capitalize transition-colors ${
                period === p ? 'bg-brand-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard
          label="Total Calls"
          value={stats?.total_calls ?? '—'}
          sub={`${stats?.inbound ?? 0} inbound · ${stats?.outbound ?? 0} outbound`}
          icon={PhoneIcon}
          color="brand"
        />
        <StatsCard
          label="Appointments Booked"
          value={stats?.booked ?? '—'}
          sub={stats?.booking_rate_pct != null ? `${stats.booking_rate_pct}% booking rate` : ''}
          icon={CalendarDaysIcon}
          color="green"
        />
        <StatsCard
          label="Missed Calls"
          value={stats?.missed ?? '—'}
          sub="Auto-callback queued"
          icon={PhoneXMarkIcon}
          color="red"
        />
        <StatsCard
          label="Avg Duration"
          value={stats?.avg_duration_minutes != null ? `${stats.avg_duration_minutes} min` : '—'}
          icon={ClockIcon}
          color="yellow"
        />
      </div>

      {/* Today's appointments */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-white">Today's Appointments</h2>
          <span className="text-xs text-gray-500">{appointments.length} scheduled</span>
        </div>
        <AppointmentTable appointments={appointments} onRefresh={fetchAppts} />
      </div>
    </div>
  )
}
