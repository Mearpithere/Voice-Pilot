import clsx from 'clsx'

const variants = {
  booked:    'bg-green-900/50 text-green-400 border-green-800',
  missed:    'bg-red-900/50 text-red-400 border-red-800',
  faq:       'bg-blue-900/50 text-blue-400 border-blue-800',
  transferred: 'bg-yellow-900/50 text-yellow-400 border-yellow-800',
  cancelled: 'bg-gray-800 text-gray-400 border-gray-700',
  unknown:   'bg-gray-800 text-gray-500 border-gray-700',
  inbound:   'bg-indigo-900/50 text-indigo-400 border-indigo-800',
  outbound:  'bg-purple-900/50 text-purple-400 border-purple-800',
  scheduled: 'bg-blue-900/50 text-blue-400 border-blue-800',
  confirmed: 'bg-green-900/50 text-green-400 border-green-800',
  completed: 'bg-gray-800 text-gray-400 border-gray-700',
  no_show:   'bg-orange-900/50 text-orange-400 border-orange-800',
}

export default function Badge({ value, label }) {
  const cls = variants[value] || variants.unknown
  return (
    <span className={clsx('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border', cls)}>
      {label || value}
    </span>
  )
}
