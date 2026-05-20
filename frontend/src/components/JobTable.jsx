import StatusBadge from './StatusBadge'
import { cvUrl, letterUrl } from '../api/client'

export default function JobTable({ jobs, selected, onToggle, onToggleAll, docs, onMarkApplied }) {
  const allSelected = jobs.length > 0 && jobs.every(j => selected.has(j.row_index))
  const someSelected = jobs.some(j => selected.has(j.row_index))

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            <th className="px-3 py-3 text-left w-10">
              <input
                type="checkbox"
                className="rounded border-gray-300 text-blue-600"
                checked={allSelected}
                ref={el => { if (el) el.indeterminate = !allSelected && someSelected }}
                onChange={e => onToggleAll(e.target.checked)}
              />
            </th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600 whitespace-nowrap">Company</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600">Job Title</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600 whitespace-nowrap">Nature</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600 whitespace-nowrap">Deadline</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600">Method</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600">Status</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600">Docs</th>
            <th className="px-3 py-3 text-left font-semibold text-gray-600">Links</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {jobs.length === 0 && (
            <tr>
              <td colSpan={9} className="px-3 py-8 text-center text-gray-400 italic">
                No jobs found. Scrape some first.
              </td>
            </tr>
          )}
          {jobs.map(job => {
            const doc = docs?.[job.row_index]
            const isSelected = selected.has(job.row_index)
            return (
              <tr
                key={job.row_index}
                className={`transition-colors ${isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'}`}
              >
                <td className="px-3 py-2.5">
                  <input
                    type="checkbox"
                    className="rounded border-gray-300 text-blue-600"
                    checked={isSelected}
                    onChange={() => onToggle(job.row_index)}
                  />
                </td>
                <td className="px-3 py-2.5 font-medium max-w-[160px] truncate" title={job.company}>
                  {job.company}
                </td>
                <td className="px-3 py-2.5 max-w-[200px] truncate" title={job.job_title}>
                  {job.job_title}
                </td>
                <td className="px-3 py-2.5 text-gray-500 max-w-[140px] truncate text-xs" title={job.job_nature}>
                  {job.job_nature}
                </td>
                <td className="px-3 py-2.5 whitespace-nowrap text-gray-600 text-xs">
                  {job.deadline || '—'}
                </td>
                <td className="px-3 py-2.5">
                  {job.email ? (
                    <span className="text-xs text-blue-600 font-medium">Email</span>
                  ) : (
                    <span className="text-xs text-gray-400">Manual</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
                  <div className="flex items-center gap-1.5">
                    <StatusBadge applied={job.applied} />
                    {String(job.applied).toLowerCase() !== 'true' && String(job.applied).toLowerCase() !== 'no email' && (
                      <button
                        onClick={() => onMarkApplied(job.row_index)}
                        className="text-xs text-gray-400 hover:text-green-600 underline"
                        title="Mark as applied"
                      >
                        mark
                      </button>
                    )}
                  </div>
                </td>
                <td className="px-3 py-2.5">
                  {doc ? (
                    <div className="flex gap-2 text-xs">
                      <a href={cvUrl(doc.cv_file)} download
                        className="text-blue-600 hover:underline font-medium">CV</a>
                      <a href={letterUrl(doc.letter_file)} download
                        className="text-blue-600 hover:underline font-medium">Letter</a>
                    </div>
                  ) : (
                    <span className="text-gray-300 text-xs">—</span>
                  )}
                </td>
                <td className="px-3 py-2.5">
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
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
