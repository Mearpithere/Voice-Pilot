export default function TranscriptViewer({ transcript }) {
  if (!transcript) {
    return <p className="text-sm text-gray-500 italic">No transcript available.</p>
  }

  const lines = transcript.split('\n').filter(Boolean)

  return (
    <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
      {lines.map((line, i) => {
        const isAI = /^(AI|Maya|Assistant):/i.test(line)
        const isUser = /^(User|Patient|Caller):/i.test(line)
        const text = line.replace(/^[^:]+:\s*/, '')

        if (!isAI && !isUser) {
          return <p key={i} className="text-xs text-gray-600 text-center">{line}</p>
        }

        return (
          <div key={i} className={`flex ${isAI ? 'justify-start' : 'justify-end'}`}>
            <div className={`max-w-[80%] px-3 py-2 rounded-xl text-sm ${
              isAI
                ? 'bg-gray-800 text-gray-200 rounded-tl-none'
                : 'bg-brand-600/30 text-brand-100 rounded-tr-none border border-brand-700/50'
            }`}>
              <p className={`text-xs font-medium mb-1 ${isAI ? 'text-brand-400' : 'text-gray-400'}`}>
                {isAI ? 'Maya (AI)' : 'Patient'}
              </p>
              {text}
            </div>
          </div>
        )
      })}
    </div>
  )
}
