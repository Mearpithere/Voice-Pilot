import { useEffect, useState } from 'react'
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline'
import { getClinic, updateClinic } from '../api/clinicsApi'
import useAuthStore from '../store/authStore'
import toast from 'react-hot-toast'
import Spinner from '../components/ui/Spinner'

export default function ClinicSettings() {
  const { clinic: ctxClinic, updateClinic: updateCtx } = useAuthStore()
  const [clinic, setClinic] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!ctxClinic?.id) return
    getClinic(ctxClinic.id)
      .then(({ data }) => setClinic(data))
      .finally(() => setLoading(false))
  }, [ctxClinic?.id])

  const set = (key, val) => setClinic((c) => ({ ...c, [key]: val }))

  const addFAQ = () => set('custom_faqs', [...(clinic.custom_faqs || []), { q: '', a: '' }])
  const removeFAQ = (i) => set('custom_faqs', clinic.custom_faqs.filter((_, idx) => idx !== i))
  const updateFAQ = (i, field, val) => {
    const faqs = [...(clinic.custom_faqs || [])]
    faqs[i] = { ...faqs[i], [field]: val }
    set('custom_faqs', faqs)
  }

  const save = async () => {
    setSaving(true)
    try {
      const { data } = await updateClinic(clinic.id, {
        name: clinic.name,
        timezone: clinic.timezone,
        business_hours_start: clinic.business_hours_start,
        business_hours_end: clinic.business_hours_end,
        after_hours_message: clinic.after_hours_message,
        custom_faqs: clinic.custom_faqs,
        google_calendar_id: clinic.google_calendar_id,
        airtable_table_name: clinic.airtable_table_name,
      })
      updateCtx(data)
      toast.success('Settings saved')
    } catch {
      toast.error('Failed to save settings')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="flex justify-center py-20"><Spinner /></div>
  if (!clinic) return <p className="p-6 text-gray-400">No clinic found.</p>

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <h1 className="text-xl font-bold text-white">Clinic Settings</h1>

      {/* Basic info */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white">Basic Info</h2>
        <Field label="Clinic Name">
          <input className="input" value={clinic.name} onChange={(e) => set('name', e.target.value)} />
        </Field>
        <Field label="Phone Number (provisioned)">
          <input className="input bg-gray-700 cursor-not-allowed" value={clinic.phone_number || 'Not provisioned'} readOnly />
        </Field>
        <Field label="Timezone">
          <input className="input" value={clinic.timezone} onChange={(e) => set('timezone', e.target.value)} placeholder="Asia/Kolkata" />
        </Field>
      </div>

      {/* Business hours */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white">Business Hours</h2>
        <div className="grid grid-cols-2 gap-4">
          <Field label="Opens">
            <input type="time" className="input" value={clinic.business_hours_start} onChange={(e) => set('business_hours_start', e.target.value)} />
          </Field>
          <Field label="Closes">
            <input type="time" className="input" value={clinic.business_hours_end} onChange={(e) => set('business_hours_end', e.target.value)} />
          </Field>
        </div>
        <Field label="After-hours message (AI reads this)">
          <textarea
            className="input min-h-20 resize-none"
            value={clinic.after_hours_message}
            onChange={(e) => set('after_hours_message', e.target.value)}
          />
        </Field>
      </div>

      {/* Integrations */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white">Integrations</h2>
        <Field label="Google Calendar ID">
          <input className="input" value={clinic.google_calendar_id || ''} onChange={(e) => set('google_calendar_id', e.target.value)} placeholder="abc@group.calendar.google.com" />
        </Field>
        <Field label="Airtable Table Name">
          <input className="input" value={clinic.airtable_table_name || ''} onChange={(e) => set('airtable_table_name', e.target.value)} placeholder="Calls" />
        </Field>
      </div>

      {/* FAQs */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Custom FAQs</h2>
          <button onClick={addFAQ} className="btn-ghost text-xs gap-1">
            <PlusIcon className="w-3.5 h-3.5" /> Add FAQ
          </button>
        </div>
        <p className="text-xs text-gray-500">These are injected into the AI's system prompt. Keep answers concise.</p>
        {(clinic.custom_faqs || []).length === 0 && (
          <p className="text-sm text-gray-600 italic">No FAQs yet.</p>
        )}
        {(clinic.custom_faqs || []).map((faq, i) => (
          <div key={i} className="bg-gray-800 rounded-lg p-3 space-y-2">
            <div className="flex items-start gap-2">
              <div className="flex-1 space-y-2">
                <input
                  className="input text-xs"
                  placeholder="Question e.g. What are your timings?"
                  value={faq.q}
                  onChange={(e) => updateFAQ(i, 'q', e.target.value)}
                />
                <textarea
                  className="input text-xs resize-none min-h-14"
                  placeholder="Answer e.g. We are open Monday to Saturday, 9am to 6pm."
                  value={faq.a}
                  onChange={(e) => updateFAQ(i, 'a', e.target.value)}
                />
              </div>
              <button onClick={() => removeFAQ(i)} className="text-gray-600 hover:text-red-400 mt-1 transition-colors">
                <TrashIcon className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>

      <button onClick={save} disabled={saving} className="btn-primary px-6">
        {saving ? 'Saving…' : 'Save Settings'}
      </button>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-gray-400 mb-1.5">{label}</label>
      {children}
    </div>
  )
}
