export default function StatsCard({ label, value, sub, icon: Icon, color = 'brand' }) {
  const colors = {
    brand:  'text-brand-400 bg-brand-900/30',
    green:  'text-green-400 bg-green-900/30',
    red:    'text-red-400 bg-red-900/30',
    yellow: 'text-yellow-400 bg-yellow-900/30',
  }
  return (
    <div className="card flex items-start gap-4">
      {Icon && (
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
      )}
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-white mt-0.5">{value ?? '—'}</p>
        {sub && <p className="text-xs text-gray-500 mt-0.5">{sub}</p>}
      </div>
    </div>
  )
}
