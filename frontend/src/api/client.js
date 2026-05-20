const BASE = '/api'

async function req(method, path, body) {
  const opts = {
    method,
    headers: body instanceof FormData ? {} : { 'Content-Type': 'application/json' },
    body: body instanceof FormData ? body : body ? JSON.stringify(body) : undefined,
  }
  const res = await fetch(`${BASE}${path}`, opts)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(text || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  getJobs: () => req('GET', '/jobs'),
  markApplied: (rowIndex) => req('PATCH', `/jobs/${rowIndex}/apply`),
  sendEmails: (rowIndices) => req('POST', '/email/send', { row_indices: rowIndices }),
  getConfig: () => req('GET', '/config'),
  updateConfig: (data) => req('PUT', '/config', data),
  uploadCV: (file) => {
    const fd = new FormData(); fd.append('file', file)
    return req('POST', '/config/cv', fd)
  },
  uploadDataLake: (file) => {
    const fd = new FormData(); fd.append('file', file)
    return req('POST', '/config/datalake', fd)
  },
}

export function scrapeSSE(filters, pages, onEvent) {
  const ctrl = new AbortController()
  fetch(`${BASE}/jobs/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filters, pages }),
    signal: ctrl.signal,
  }).then(async (res) => {
    if (!res.ok) {
      const text = await res.text()
      onEvent({ type: 'error', message: text })
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const evt = JSON.parse(line.slice(6))
            onEvent(evt)
          } catch {}
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onEvent({ type: 'error', message: err.message })
  })
  return () => ctrl.abort()
}

export function processSSE(rowIndices, onEvent) {
  const ctrl = new AbortController()
  fetch(`${BASE}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ row_indices: rowIndices }),
    signal: ctrl.signal,
  }).then(async (res) => {
    if (!res.ok) {
      const text = await res.text()
      onEvent({ type: 'error', message: text })
      return
    }
    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const evt = JSON.parse(line.slice(6))
            onEvent(evt)
          } catch {}
        }
      }
    }
  }).catch((err) => {
    if (err.name !== 'AbortError') onEvent({ type: 'error', message: err.message })
  })
  return () => ctrl.abort()
}

export function cvUrl(filename) { return `${BASE}/documents/cv/${encodeURIComponent(filename)}` }
export function letterUrl(filename) { return `${BASE}/documents/letter/${encodeURIComponent(filename)}` }
