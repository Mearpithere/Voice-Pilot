import { useState } from 'react'
import { ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline'
import useAuthStore from '../store/authStore'
import WebCallButton from '../components/widget/WebCallButton'
import toast from 'react-hot-toast'

export default function WidgetEmbed() {
  const clinic = useAuthStore((s) => s.clinic)
  const [copied, setCopied] = useState(false)

  const snippetUrl = `${window.location.origin}/widget.js`
  const snippet = `<!-- VoicePilot Web Call Widget -->
<script
  src="${snippetUrl}"
  data-clinic-id="${clinic?.id || 'YOUR_CLINIC_ID'}"
  data-position="bottom-right"
  data-label="Call Us"
></script>`

  const copy = () => {
    navigator.clipboard.writeText(snippet)
    setCopied(true)
    toast.success('Copied to clipboard')
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="p-6 max-w-2xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-white">Web Call Widget</h1>
        <p className="text-sm text-gray-400 mt-1">
          Embed this on your clinic website so patients can call directly from their browser — no phone needed.
        </p>
      </div>

      {/* Live preview */}
      <div className="card space-y-4">
        <h2 className="text-sm font-semibold text-white">Live Preview</h2>
        <div className="bg-gray-800 rounded-xl p-10 flex flex-col items-center justify-center gap-2 min-h-40">
          <p className="text-xs text-gray-500 mb-4">This is how the button looks on your website</p>
          <WebCallButton preview />
        </div>
      </div>

      {/* Embed code */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-white">Embed Code</h2>
          <button onClick={copy} className="btn-ghost text-xs gap-1.5">
            {copied ? <CheckIcon className="w-3.5 h-3.5 text-green-400" /> : <ClipboardDocumentIcon className="w-3.5 h-3.5" />}
            {copied ? 'Copied!' : 'Copy'}
          </button>
        </div>
        <pre className="bg-gray-800 rounded-lg p-4 text-xs text-gray-300 overflow-x-auto leading-relaxed whitespace-pre-wrap">
          {snippet}
        </pre>
        <p className="text-xs text-gray-500">
          Paste this snippet just before the <code className="text-gray-400">&lt;/body&gt;</code> tag of your website.
        </p>
      </div>

      {/* Instructions */}
      <div className="card space-y-3">
        <h2 className="text-sm font-semibold text-white">How it works</h2>
        <ol className="space-y-2 text-sm text-gray-400 list-decimal list-inside">
          <li>Patient clicks the button on your website</li>
          <li>Browser asks for microphone permission</li>
          <li>Patient is connected directly to Maya (your AI receptionist)</li>
          <li>Call is logged in your dashboard like any regular call</li>
        </ol>
      </div>
    </div>
  )
}
