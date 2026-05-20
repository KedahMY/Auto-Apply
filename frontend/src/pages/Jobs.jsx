import { useEffect, useRef, useState } from 'react'
import { api, processSSE } from '../api/client'
import JobTable from '../components/JobTable'
import ProgressLog from '../components/ProgressLog'

const STEP_LABELS = {
  cv_tailoring: 'Tailoring CV...',
  cv_building: 'Building CV DOCX...',
  letter_generating: 'Generating cover letter...',
  letter_building: 'Building cover letter DOCX...',
}

export default function Jobs() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState(new Set())
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  // Document generation state
  const [processing, setProcessing] = useState(false)
  const [processLog, setProcessLog] = useState([])
  const [docs, setDocs] = useState({}) // row_index → {cv_file, letter_file}
  const [allDone, setAllDone] = useState(false)
  const stopRef = useRef(null)

  // Apply panel state
  const [sending, setSending] = useState(false)
  const [sendResults, setSendResults] = useState([])
  const [showApply, setShowApply] = useState(false)

  function reload() {
    setLoading(true)
    api.getJobs().then(data => { setJobs(data); setLoading(false) }).catch(console.error)
  }

  useEffect(() => { reload() }, [])

  const filtered = jobs.filter(j => {
    const matchSearch = !search ||
      j.company.toLowerCase().includes(search.toLowerCase()) ||
      j.job_title.toLowerCase().includes(search.toLowerCase())
    const appVal = String(j.applied).toLowerCase()
    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'pending' && (appVal === 'false' || appVal === 'no email')) ||
      (statusFilter === 'applied' && appVal === 'true') ||
      (statusFilter === 'email' && !!j.email)
    return matchSearch && matchStatus
  })

  function toggleJob(idx) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  function toggleAll(checked) {
    setSelected(checked ? new Set(filtered.map(j => j.row_index)) : new Set())
  }

  async function handleMarkApplied(rowIndex) {
    await api.markApplied(rowIndex)
    reload()
  }

  function addLog(entry) {
    setProcessLog(prev => [...prev, entry])
  }

  function handleGenerate() {
    const indices = [...selected]
    if (indices.length === 0) return
    setProcessing(true)
    setAllDone(false)
    setSendResults([])
    setShowApply(false)
    setProcessLog([{ type: 'info', text: `Starting document generation for ${indices.length} job(s)...` }])

    const stop = processSSE(indices, (evt) => {
      if (evt.type === 'ping') return
      if (evt.type === 'step') {
        addLog({ type: 'info', text: `  [${evt.n}/${evt.total}] ${evt.company} — ${evt.title}: ${STEP_LABELS[evt.step] || evt.step}` })
      } else if (evt.type === 'job_done') {
        addLog({ type: 'job_done', text: `  ✓ [${evt.n}/${evt.total}] ${evt.company} — ${evt.title} done` })
        setDocs(prev => ({ ...prev, [evt.row_index]: { cv_file: evt.cv_file, letter_file: evt.letter_file } }))
      } else if (evt.type === 'all_done') {
        addLog({ type: 'all_done', text: '✓ All documents generated. Review and send applications below.' })
        setProcessing(false)
        setAllDone(true)
        setShowApply(true)
        reload()
      } else if (evt.type === 'error') {
        addLog({ type: 'error', text: `✗ Error: ${evt.message}` })
        setProcessing(false)
      }
    })

    stopRef.current = stop
  }

  async function handleSendEmails() {
    const emailJobs = selectedJobsList.filter(j => j.email && docs[j.row_index])
    if (emailJobs.length === 0) return
    setSending(true)
    try {
      const result = await api.sendEmails(emailJobs.map(j => j.row_index))
      setSendResults(result.results)
      reload()
    } catch (e) {
      setSendResults([{ ok: false, error: e.message }])
    } finally {
      setSending(false)
    }
  }

  const selectedJobsList = jobs.filter(j => selected.has(j.row_index))
  const emailJobs = selectedJobsList.filter(j => j.email && docs[j.row_index])
  const manualJobs = selectedJobsList.filter(j => !j.email && docs[j.row_index])
  const pendingEmailJobs = selectedJobsList.filter(j => j.email)
  const selectedCount = selected.size

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Jobs</h2>
          <p className="text-sm text-gray-500 mt-0.5">{jobs.length} total jobs tracked</p>
        </div>
        <button onClick={reload} className="text-sm text-gray-400 hover:text-gray-600">↻ Refresh</button>
      </div>

      {/* Search + filter bar */}
      <div className="flex gap-3">
        <input
          type="text"
          placeholder="Search company or title..."
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />
        <select
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
          value={statusFilter}
          onChange={e => setStatusFilter(e.target.value)}
        >
          <option value="all">All</option>
          <option value="pending">Not applied</option>
          <option value="applied">Applied</option>
          <option value="email">Has email</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <p className="text-center py-10 text-gray-400">Loading jobs...</p>
      ) : (
        <JobTable
          jobs={filtered}
          selected={selected}
          onToggle={toggleJob}
          onToggleAll={toggleAll}
          docs={docs}
          onMarkApplied={handleMarkApplied}
        />
      )}

      {/* Selection action bar */}
      {selectedCount > 0 && (
        <div className="sticky bottom-4 bg-white border border-gray-200 rounded-xl shadow-lg px-5 py-4 flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">
            {selectedCount} job{selectedCount !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={handleGenerate}
            disabled={processing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {processing ? '⏳ Generating...' : '✨ Generate Documents'}
          </button>
          {allDone && (
            <button
              onClick={() => setShowApply(v => !v)}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-semibold hover:bg-green-700 transition-colors"
            >
              📨 Send Applications
            </button>
          )}
          <button
            onClick={() => setSelected(new Set())}
            className="ml-auto text-sm text-gray-400 hover:text-gray-600"
          >
            Clear selection
          </button>
        </div>
      )}

      {/* Process log */}
      {processLog.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 mb-3">Generation Progress</h3>
          <ProgressLog lines={processLog} className="h-48" />
        </div>
      )}

      {/* Apply panel */}
      {showApply && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5 space-y-5">
          <h3 className="font-semibold text-gray-800 text-lg">Send Applications</h3>

          {emailJobs.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-blue-500 rounded-full inline-block" />
                Auto-send via email ({emailJobs.length})
              </h4>
              <div className="space-y-2 mb-4">
                {emailJobs.map(j => (
                  <div key={j.row_index} className="flex items-center gap-3 text-sm p-3 bg-blue-50 rounded-lg">
                    <div className="flex-1">
                      <span className="font-medium">{j.company}</span>
                      <span className="text-gray-500 mx-1.5">—</span>
                      {j.job_title}
                    </div>
                    <span className="text-blue-600 text-xs">{j.email}</span>
                    {sendResults.find(r => r.row_index === j.row_index)?.ok === true && (
                      <span className="text-green-600 text-xs font-medium">✓ Sent</span>
                    )}
                    {sendResults.find(r => r.row_index === j.row_index)?.ok === false && (
                      <span className="text-red-600 text-xs font-medium">
                        ✗ {sendResults.find(r => r.row_index === j.row_index).error}
                      </span>
                    )}
                  </div>
                ))}
              </div>
              <button
                onClick={handleSendEmails}
                disabled={sending || sendResults.some(r => r.ok)}
                className="px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {sending ? 'Sending...' : `📧 Send ${emailJobs.length} Email${emailJobs.length !== 1 ? 's' : ''}`}
              </button>
            </div>
          )}

          {manualJobs.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
                <span className="w-2 h-2 bg-gray-400 rounded-full inline-block" />
                Manual application required ({manualJobs.length})
              </h4>
              <div className="space-y-2">
                {manualJobs.map(j => (
                  <div key={j.row_index} className="p-3 bg-gray-50 rounded-lg text-sm space-y-1">
                    <div className="font-medium">{j.company} — {j.job_title}</div>
                    {j.website && (
                      <a href={j.website} target="_blank" rel="noreferrer"
                        className="text-blue-600 hover:underline block text-xs">
                        {j.website}
                      </a>
                    )}
                    {j.detail_url && !j.website && (
                      <a href={j.detail_url} target="_blank" rel="noreferrer"
                        className="text-blue-600 hover:underline block text-xs">
                        HKUST Portal →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {pendingEmailJobs.length > 0 && emailJobs.length === 0 && (
            <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
              ⚠ {pendingEmailJobs.length} email job(s) selected but documents haven't been generated yet. Generate documents first.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
