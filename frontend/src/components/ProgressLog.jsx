import { useEffect, useRef } from 'react'

export default function ProgressLog({ lines, className = '' }) {
  const endRef = useRef(null)
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [lines])

  return (
    <div className={`bg-gray-900 rounded-lg p-4 font-mono text-sm overflow-y-auto ${className}`}>
      {lines.length === 0 && (
        <p className="text-gray-500 italic">Waiting to start...</p>
      )}
      {lines.map((line, i) => (
        <div key={i} className={`leading-5 ${
          line.type === 'error' ? 'text-red-400' :
          line.type === 'warning' ? 'text-yellow-400' :
          line.type === 'done' || line.type === 'all_done' || line.type === 'job_done' ? 'text-green-400' :
          line.type === 'info' ? 'text-blue-400' :
          'text-gray-300'
        }`}>
          {line.text}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}
