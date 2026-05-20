import { format } from 'date-fns'
import { CalendarDaysIcon, CheckCircleIcon } from '@heroicons/react/24/outline'
import { updateAppointment, resendWhatsApp } from '../../api/appointmentsApi'
import toast from 'react-hot-toast'
import Badge from '../ui/Badge'

export default function AppointmentTable({ appointments, onRefresh }) {
  if (!appointments?.length) {
    return (
      <div className="text-center py-16 text-gray-500">
        <CalendarDaysIcon className="w-10 h-10 mx-auto mb-3 opacity-30" />
        <p className="text-sm">No appointments found.</p>
      </div>
    )
  }

  const handleStatus = async (id, newStatus) => {
    try {
      await updateAppointment(id, { status: newStatus })
      toast.success(`Marked as ${newStatus}`)
      onRefresh?.()
    } catch {
      toast.error('Update failed')
    }
  }

  const handleResend = async (id) => {
    try {
      await resendWhatsApp(id)
      toast.success('WhatsApp confirmation queued')
    } catch {
      toast.error('Failed to resend')
    }
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
            <th className="text-left px-4 py-3 font-medium">Patient</th>
            <th className="text-left px-4 py-3 font-medium">Type</th>
            <th className="text-left px-4 py-3 font-medium">Date & Time</th>
            <th className="text-left px-4 py-3 font-medium">Status</th>
            <th className="text-left px-4 py-3 font-medium">WA Sent</th>
            <th className="text-left px-4 py-3 font-medium">Actions</th>
          </tr>
        </thead>
        <tbody>
          {appointments.map((appt) => (
            <tr key={appt.id} className="border-b border-gray-800 hover:bg-gray-800/40">
              <td className="px-4 py-3">
                <p className="font-medium text-white">{appt.patient_name}</p>
                <p className="text-xs text-gray-500">{appt.patient_phone}</p>
              </td>
              <td className="px-4 py-3 text-gray-300">{appt.appointment_type}</td>
              <td className="px-4 py-3 text-gray-400 text-xs">
                {format(new Date(appt.scheduled_start), 'dd MMM yyyy')}<br />
                {format(new Date(appt.scheduled_start), 'h:mm a')}
              </td>
              <td className="px-4 py-3">
                <Badge value={appt.status} label={appt.status_display} />
              </td>
              <td className="px-4 py-3">
                {appt.whatsapp_sent
                  ? <CheckCircleIcon className="w-4 h-4 text-green-400" />
                  : <span className="text-xs text-gray-600">—</span>}
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-2 flex-wrap">
                  {appt.status === 'scheduled' && (
                    <>
                      <button
                        onClick={() => handleStatus(appt.id, 'confirmed')}
                        className="text-xs text-green-400 hover:text-green-300"
                      >Confirm</button>
                      <button
                        onClick={() => handleStatus(appt.id, 'cancelled')}
                        className="text-xs text-red-400 hover:text-red-300"
                      >Cancel</button>
                    </>
                  )}
                  {!appt.whatsapp_sent && (
                    <button
                      onClick={() => handleResend(appt.id)}
                      className="text-xs text-blue-400 hover:text-blue-300"
                    >Resend WA</button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
