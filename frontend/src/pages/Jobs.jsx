import { useEffect, useRef, useState } from 'react'
import { api, processSSE, cvUrl, letterUrl, cvPreviewUrl, letterPreviewUrl } from '../api/client'
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
  const [sortBy, setSortBy] = useState('recent')

  // Document generation state
  const [processing, setProcessing] = useState(false)
  const [processLog, setProcessLog] = useState([])
  const [docs, setDocs] = useState({}) // row_index → {cv_file, letter_file}
  const [allDone, setAllDone] = useState(false)
  const stopRef = useRef(null)

  // Per-job regeneration state
  const [regenLoading, setRegenLoading] = useState({}) // row_index → bool

  // Preview modal state: null | {title, url, iframeLoading}
  const [previewModal, setPreviewModal] = useState(null)

  // Apply panel state
  const [sending, setSending] = useState(false)
  const [sendResults, setSendResults] = useState([])
  const [showApply, setShowApply] = useState(false)

  function reload() {
    setLoading(true)
    api.getJobs().then(data => { setJobs(data); setLoading(false) }).catch(console.error)
  }

  useEffect(() => { reload() }, [])

  // Rebuild docs from server data after every jobs reload so links survive refresh/navigation
  useEffect(() => {
    const fromServer = {}
    jobs.forEach(j => {
      if (j.cv_file && j.letter_file) {
        fromServer[j.row_index] = { cv_file: j.cv_file, letter_file: j.letter_file }
      }
    })
    setDocs(fromServer)
  }, [jobs])


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

  const sorted = [...filtered].sort((a, b) => {
    if (sortBy === 'recent') {
      const da = new Date(b.posting_date), db = new Date(a.posting_date)
      if (isNaN(da) && isNaN(db)) return 0
      if (isNaN(da)) return 1
      if (isNaN(db)) return -1
      return da - db
    } else {
      const da = new Date(a.deadline), db = new Date(b.deadline)
      if (isNaN(da) && isNaN(db)) return 0
      if (isNaN(da)) return 1
      if (isNaN(db)) return -1
      return da - db
    }
  })

  function toggleJob(idx) {
    setSelected(prev => {
      const next = new Set(prev)
      next.has(idx) ? next.delete(idx) : next.add(idx)
      return next
    })
  }

  function toggleAll(checked) {
    setSelected(checked ? new Set(sorted.map(j => j.row_index)) : new Set())
  }

  async function handleMarkApplied(rowIndex) {
    try {
      await api.markApplied(rowIndex)
      reload()
    } catch (e) {
      console.error('Mark applied failed:', e)
    }
  }

  async function handleDeleteJob(rowIndex) {
    await api.deleteJob(rowIndex)
    setSelected(prev => { const n = new Set(prev); n.delete(rowIndex); return n })
    setDocs(prev => { const n = { ...prev }; delete n[rowIndex]; return n })
    reload()
  }

  async function handleDeleteAll() {
    if (!window.confirm(`Delete all ${jobs.length} jobs? This cannot be undone.`)) return
    await api.deleteAllJobs()
    setSelected(new Set())
    setDocs({})
    setAllDone(false)
    setProcessLog([])
    setShowApply(false)
    reload()
  }

  function addLog(entry) {
    setProcessLog(prev => [...prev, entry])
  }

  function runGenerate(indices, onDone) {
    const stop = processSSE(indices, (evt) => {
      if (evt.type === 'ping') return
      if (evt.type === 'step') {
        addLog({ type: 'info', text: `  [${evt.n}/${evt.total}] ${evt.company} — ${evt.title}: ${STEP_LABELS[evt.step] || evt.step}` })
      } else if (evt.type === 'job_done') {
        addLog({ type: 'job_done', text: `  ✓ [${evt.n}/${evt.total}] ${evt.company} — ${evt.title} done` })
        setDocs(prev => ({ ...prev, [evt.row_index]: { cv_file: evt.cv_file, letter_file: evt.letter_file } }))
      } else if (evt.type === 'all_done') {
        if (onDone) onDone()
      } else if (evt.type === 'error') {
        addLog({ type: 'error', text: `✗ Error: ${evt.message}` })
        if (onDone) onDone(true)
      }
    })
    return stop
  }

  function handleGenerate() {
    const indices = [...selected]
    if (indices.length === 0) return
    setProcessing(true)
    setAllDone(false)
    setSendResults([])
    setShowApply(false)
    setProcessLog([{ type: 'info', text: `Starting document generation for ${indices.length} job(s)...` }])

    const stop = runGenerate(indices, (isError) => {
      setProcessing(false)
      if (!isError) {
        addLog({ type: 'all_done', text: '✓ All documents generated. Review below.' })
        setAllDone(true)
        setShowApply(true)
        reload()
      }
    })
    stopRef.current = stop
  }

  function handleRegenerate(rowIndex) {
    setRegenLoading(prev => ({ ...prev, [rowIndex]: true }))
    runGenerate([rowIndex], () => {
      setRegenLoading(prev => ({ ...prev, [rowIndex]: false }))
      reload()
    })
  }

  function openPreview(filename, type, title) {
    const url = type === 'cv' ? cvPreviewUrl(filename) : letterPreviewUrl(filename)
    setPreviewModal({ title, url, iframeLoading: true })
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
  const generatedEntries = Object.entries(docs)

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Jobs</h2>
          <p className="text-sm text-gray-500 mt-0.5">{jobs.length} total jobs tracked</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={reload} className="text-sm text-gray-400 hover:text-gray-600">↻ Refresh</button>
          {jobs.length > 0 && (
            <button onClick={handleDeleteAll}
              className="text-sm text-red-400 hover:text-red-600 border border-red-200 hover:border-red-400 rounded-lg px-3 py-1.5 transition-colors">
              Delete All
            </button>
          )}
        </div>
      </div>

      {/* Sort + filter bar */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="flex rounded-lg border border-gray-200 overflow-hidden text-sm">
          <button
            onClick={() => setSortBy('recent')}
            className={`px-3 py-2 transition-colors ${sortBy === 'recent' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
          >
            Most Recent
          </button>
          <button
            onClick={() => setSortBy('deadline')}
            className={`px-3 py-2 border-l border-gray-200 transition-colors ${sortBy === 'deadline' ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 hover:bg-gray-50'}`}
          >
            By Deadline
          </button>
        </div>
        <input
          type="text"
          placeholder="Search company or title..."
          className="flex-1 min-w-[180px] border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
          jobs={sorted}
          selected={selected}
          onToggle={toggleJob}
          onToggleAll={toggleAll}
          docs={docs}
          onMarkApplied={handleMarkApplied}
          onDelete={handleDeleteJob}
          onPreview={generatedEntries.length > 0 ? openPreview : null}
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

      {/* Document results */}
      {generatedEntries.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
          <h3 className="font-semibold text-gray-800 text-lg mb-4">Generated Documents</h3>
          <div className="space-y-3">
            {generatedEntries.map(([rowIndexStr, doc]) => {
              const rowIndex = parseInt(rowIndexStr)
              const job = jobs.find(j => j.row_index === rowIndex)
              if (!job) return null
              const isRegen = regenLoading[rowIndex]
              return (
                <div key={rowIndex} className="p-4 bg-gray-50 rounded-lg border border-gray-100">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-medium text-gray-800 flex-1 min-w-[200px]">
                      {job.company} — {job.job_title}
                    </span>
                    <button
                      onClick={() => openPreview(doc.cv_file, 'cv', `${job.company} — CV`)}
                      className="text-sm px-3 py-1.5 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      Preview CV
                    </button>
                    <button
                      onClick={() => openPreview(doc.letter_file, 'letter', `${job.company} — Cover Letter`)}
                      className="text-sm px-3 py-1.5 bg-purple-50 text-purple-700 rounded-lg hover:bg-purple-100 transition-colors"
                    >
                      Preview Letter
                    </button>
                    <a href={cvUrl(doc.cv_file)} download
                      className="text-sm px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      ↓ CV
                    </a>
                    <a href={letterUrl(doc.letter_file)} download
                      className="text-sm px-3 py-1.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                      ↓ Letter
                    </a>
                    <button
                      onClick={() => handleRegenerate(rowIndex)}
                      disabled={isRegen || processing}
                      className="text-sm px-3 py-1.5 bg-orange-50 text-orange-700 rounded-lg hover:bg-orange-100 disabled:opacity-50 transition-colors"
                    >
                      {isRegen ? '⏳ Regenerating...' : '↺ Regenerate'}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
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

      {/* Document preview modal — renders Word-accurate PDF via iframe */}
      {previewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="bg-white rounded-xl shadow-2xl flex flex-col overflow-hidden" style={{ width: '92vw', maxWidth: '960px', height: '92vh' }}>
            <div className="px-5 py-3 border-b border-gray-200 flex items-center justify-between shrink-0">
              <h3 className="font-semibold text-gray-800 truncate">{previewModal.title}</h3>
              <button
                onClick={() => setPreviewModal(null)}
                className="ml-4 text-gray-400 hover:text-gray-700 text-2xl leading-none shrink-0"
              >
                ×
              </button>
            </div>
            <div className="flex-1 relative">
              {previewModal.iframeLoading && (
                <div className="absolute inset-0 flex flex-col items-center justify-center bg-white z-10 gap-2">
                  <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  <p className="text-sm text-gray-400">Converting to PDF…</p>
                </div>
              )}
              <iframe
                src={previewModal.url}
                className="w-full h-full border-0"
                title={previewModal.title}
                onLoad={() => setPreviewModal(prev => prev ? { ...prev, iframeLoading: false } : null)}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
