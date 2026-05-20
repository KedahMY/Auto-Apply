import { useEffect, useState } from 'react'
import { api } from '../api/client'
import StatusBadge from '../components/StatusBadge'

function StatCard({ label, value, color }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-1 shadow-sm`}>
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wider">{label}</p>
      <p className={`text-3xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

export default function Dashboard() {
  const [jobs, setJobs] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  useEffect(() => {
    api.getJobs().then(setJobs).catch(console.error).finally(() => setLoading(false))
  }, [])

  const today = new Date()
  const applied = jobs.filter(j => String(j.applied).toLowerCase() === 'true')
  const noEmail = jobs.filter(j => String(j.applied).toLowerCase() === 'no email')
  const pending = jobs.filter(j => String(j.applied).toLowerCase() === 'false')
  const expiring = jobs.filter(j => {
    const d = new Date(j.deadline)
    if (isNaN(d)) return false
    const diff = (d - today) / 86400000
    return diff >= 0 && diff <= 7
  })

  const filtered = jobs.filter(j => {
    const matchSearch = !search ||
      j.company.toLowerCase().includes(search.toLowerCase()) ||
      j.job_title.toLowerCase().includes(search.toLowerCase())
    const appVal = String(j.applied).toLowerCase()
    const matchStatus =
      statusFilter === 'all' ||
      (statusFilter === 'applied' && appVal === 'true') ||
      (statusFilter === 'pending' && appVal === 'false') ||
      (statusFilter === 'manual' && appVal === 'no email')
    return matchSearch && matchStatus
  })

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h2>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Jobs" value={jobs.length} color="text-gray-900" />
        <StatCard label="Applied" value={applied.length} color="text-green-600" />
        <StatCard label="Pending" value={pending.length} color="text-yellow-600" />
        <StatCard label="Expiring ≤7 days" value={expiring.length} color="text-red-500" />
      </div>

      <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
        <div className="px-5 py-4 border-b border-gray-100 flex flex-col sm:flex-row gap-3">
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
            <option value="all">All statuses</option>
            <option value="applied">Applied</option>
            <option value="pending">Pending (email)</option>
            <option value="manual">Manual apply</option>
          </select>
        </div>

        {loading ? (
          <p className="px-5 py-10 text-center text-gray-400">Loading jobs...</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-gray-50 border-b border-gray-100">
                <tr>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Company</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Job Title</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Deadline</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Method</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Status</th>
                  <th className="px-4 py-3 text-left font-semibold text-gray-600">Links</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400 italic">
                      No jobs match your filters.
                    </td>
                  </tr>
                )}
                {filtered.map(job => (
                  <tr key={job.row_index} className="hover:bg-gray-50 transition-colors">
                    <td className="px-4 py-2.5 font-medium max-w-[180px] truncate" title={job.company}>
                      {job.company}
                    </td>
                    <td className="px-4 py-2.5 max-w-[220px] truncate" title={job.job_title}>
                      {job.job_title}
                    </td>
                    <td className="px-4 py-2.5 text-gray-500 text-xs whitespace-nowrap">
                      {job.deadline || '—'}
                    </td>
                    <td className="px-4 py-2.5">
                      {job.email
                        ? <span className="text-xs text-blue-600 font-medium">Email</span>
                        : <span className="text-xs text-gray-400">Manual</span>}
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusBadge applied={job.applied} />
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex gap-2 text-xs">
                        {job.detail_url && (
                          <a href={job.detail_url} target="_blank" rel="noreferrer"
                            className="text-gray-400 hover:text-blue-600">Portal</a>
                        )}
                        {job.website && (
                          <a href={job.website} target="_blank" rel="noreferrer"
                            className="text-gray-400 hover:text-blue-600">Site</a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="px-5 py-3 border-t border-gray-100 text-xs text-gray-400">
          {filtered.length} of {jobs.length} job(s)
        </div>
      </div>
    </div>
  )
}
