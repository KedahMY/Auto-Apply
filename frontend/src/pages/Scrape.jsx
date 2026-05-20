import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { scrapeSSE } from '../api/client'
import FilterPanel from '../components/FilterPanel'
import ProgressLog from '../components/ProgressLog'

export default function Scrape() {
  const [filters, setFilters] = useState({})
  const [pages, setPages] = useState('1-3')
  const [running, setRunning] = useState(false)
  const [done, setDone] = useState(false)
  const [log, setLog] = useState([])
  const stopRef = useRef(null)
  const navigate = useNavigate()

  function addLog(entry) {
    setLog(prev => [...prev, entry])
  }

  function handleScrape() {
    if (running) return
    setRunning(true)
    setDone(false)
    setLog([{ type: 'info', text: 'Connecting to HKUST job board...' }])

    const stop = scrapeSSE(filters, pages, (evt) => {
      if (evt.type === 'ping') return
      if (evt.type === 'progress') {
        addLog({ type: 'progress', text: `📄 ${evt.message}` })
      } else if (evt.type === 'job_found') {
        addLog({ type: 'info', text: `  → Found: ${evt.company} — ${evt.job_title} (${evt.count} total)` })
      } else if (evt.type === 'warning') {
        addLog({ type: 'warning', text: `⚠ ${evt.message}` })
      } else if (evt.type === 'info') {
        addLog({ type: 'info', text: `ℹ ${evt.message}` })
      } else if (evt.type === 'done') {
        addLog({ type: 'done', text: `✓ Done! ${evt.new_jobs} new job(s) saved (${evt.total} found in this scrape, ${evt.total_stored} total stored).` })
        setDone(true)
        setRunning(false)
      } else if (evt.type === 'error') {
        addLog({ type: 'error', text: `✗ Error: ${evt.message}` })
        setRunning(false)
      }
    })

    stopRef.current = stop
  }

  function handleStop() {
    stopRef.current?.()
    setRunning(false)
    addLog({ type: 'warning', text: '⚠ Scrape cancelled by user.' })
  }

  function clearFilters() {
    setFilters({})
  }

  const activeFilterCount = Object.values(filters).flat().filter(Boolean).length

  return (
    <div className="h-full flex flex-col p-6 max-w-6xl mx-auto">
      <div className="mb-4 flex-shrink-0">
        <h2 className="text-2xl font-bold text-gray-900 mb-1">Scrape Jobs</h2>
        <p className="text-sm text-gray-500">Select filters then scrape the HKUST career portal for matching jobs.</p>
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Filter panel — independently scrollable */}
        <div className="w-72 flex-shrink-0 flex flex-col min-h-0">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm flex flex-col overflow-hidden flex-1">
            <div className="flex items-center justify-between px-5 pt-5 pb-3 flex-shrink-0">
              <h3 className="font-semibold text-gray-800">Filters</h3>
              {activeFilterCount > 0 && (
                <button onClick={clearFilters} className="text-xs text-gray-400 hover:text-red-500">
                  Clear all ({activeFilterCount})
                </button>
              )}
            </div>

            <div className="px-5 pb-3 flex-shrink-0">
              <label className="text-xs font-semibold text-gray-500 uppercase tracking-wider block mb-1.5">
                Pages to scrape
              </label>
              <input
                type="text"
                value={pages}
                onChange={e => setPages(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g. 1-3 or 5"
              />
              <p className="text-xs text-gray-400 mt-1">~20 jobs per page</p>
            </div>

            <div className="px-5 pb-5 overflow-y-auto flex-1">
              <FilterPanel filters={filters} onChange={setFilters} />
            </div>
          </div>
        </div>

        {/* Right: action + log — fills remaining height */}
        <div className="flex-1 flex flex-col gap-4 min-h-0">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 flex-shrink-0">
            <div className="flex items-center gap-3">
              <button
                onClick={running ? handleStop : handleScrape}
                className={`px-5 py-2.5 rounded-lg font-semibold text-sm transition-colors ${
                  running
                    ? 'bg-red-100 text-red-700 hover:bg-red-200'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {running ? '⏹ Stop' : '🔍 Scrape Jobs'}
              </button>
              {running && (
                <span className="text-sm text-gray-500 animate-pulse">Scraping in progress...</span>
              )}
              {done && !running && (
                <button
                  onClick={() => navigate('/jobs')}
                  className="ml-auto px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700 transition-colors"
                >
                  View Jobs →
                </button>
              )}
            </div>
          </div>

          <ProgressLog lines={log} className="flex-1 min-h-0" />
        </div>
      </div>
    </div>
  )
}
