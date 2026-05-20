import { NavLink, useNavigate } from 'react-router-dom'
import {
  ChartBarIcon, PhoneArrowDownLeftIcon, CalendarDaysIcon,
  Cog6ToothIcon, SignalIcon, ArrowRightStartOnRectangleIcon,
} from '@heroicons/react/24/outline'
import useAuthStore from '../../store/authStore'
import clsx from 'clsx'

const nav = [
  { to: '/dashboard',    label: 'Dashboard',    Icon: ChartBarIcon },
  { to: '/calls',        label: 'Call Logs',    Icon: PhoneArrowDownLeftIcon },
  { to: '/appointments', label: 'Appointments', Icon: CalendarDaysIcon },
  { to: '/widget',       label: 'Web Widget',   Icon: SignalIcon },
  { to: '/settings',     label: 'Settings',     Icon: Cog6ToothIcon },
]

export default function Sidebar() {
  const { clinic, logout } = useAuthStore()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-brand-600 rounded-lg flex items-center justify-center">
            <SignalIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-white">VoicePilot</span>
        </div>
        {clinic && (
          <p className="mt-2 text-xs text-gray-500 truncate">{clinic.name}</p>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ to, label, Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800'
              )
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 py-4 border-t border-gray-800">
        <button onClick={handleLogout} className="btn-ghost w-full justify-start">
          <ArrowRightStartOnRectangleIcon className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  )
}
