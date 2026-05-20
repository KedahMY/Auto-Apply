import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

function Section({ title, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <h3 className="font-semibold text-gray-800 text-base mb-4 pb-3 border-b border-gray-100">{title}</h3>
      <div className="space-y-4">{children}</div>
    </div>
  )
}

function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      {hint && <p className="text-xs text-gray-400 mb-1.5">{hint}</p>}
      {children}
    </div>
  )
}

function Input({ value, onChange, type = 'text', placeholder }) {
  return (
    <input
      type={type}
      className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder={placeholder}
    />
  )
}

export default function Settings() {
  const [cfg, setCfg] = useState(null)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({})
  const cvRef = useRef()
  const dlRef = useRef()
  const [uploadStatus, setUploadStatus] = useState({})

  useEffect(() => {
    api.getConfig().then(data => {
      setCfg(data)
      setForm({
        dashscope_api_key: '',
        session_cookie: data.session_cookie || '',
        model_id: data.model_id || '',
        user_name: data.user_name || '',
        user_email: data.user_email || '',
        bcc_email: data.bcc_email || '',
        default_pages: data.default_pages || '1-3',
      })
    }).catch(console.error)
  }, [])

  function setField(key, val) { setForm(f => ({ ...f, [key]: val })) }

  async function handleSave() {
    setSaving(true)
    try {
      await api.updateConfig(form)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
      const fresh = await api.getConfig()
      setCfg(fresh)
    } catch (e) {
      alert('Save failed: ' + e.message)
    } finally {
      setSaving(false)
    }
  }

  async function uploadFile(ref, uploader, key) {
    const file = ref.current?.files?.[0]
    if (!file) return
    setUploadStatus(s => ({ ...s, [key]: 'uploading' }))
    try {
      await uploader(file)
      setUploadStatus(s => ({ ...s, [key]: 'done' }))
      const fresh = await api.getConfig()
      setCfg(fresh)
    } catch (e) {
      setUploadStatus(s => ({ ...s, [key]: 'error: ' + e.message }))
    }
  }

  if (!cfg) return <div className="p-6 text-gray-400">Loading...</div>

  return (
    <div className="p-6 max-w-2xl mx-auto space-y-5">
      <h2 className="text-2xl font-bold text-gray-900">Settings</h2>

      <Section title="AI Model">
        <Field label="Dashscope API Key" hint="Leave blank to keep the existing key.">
          <Input
            type="password"
            value={form.dashscope_api_key}
            onChange={v => setField('dashscope_api_key', v)}
            placeholder="sk-... (leave blank to keep existing)"
          />
        </Field>
        <Field label="Model ID">
          <Input value={form.model_id} onChange={v => setField('model_id', v)} placeholder="qwen3.6-flash" />
        </Field>
      </Section>

      <Section title="HKUST Job Board">
        <Field
          label="PHPSESSID Cookie"
          hint="Grab from browser DevTools → Application → Cookies on career.hkust.edu.hk"
        >
          <Input value={form.session_cookie} onChange={v => setField('session_cookie', v)}
            placeholder="Paste fresh session cookie here" />
        </Field>
        <Field label="Default pages to scrape">
          <Input value={form.default_pages} onChange={v => setField('default_pages', v)} placeholder="1-3" />
        </Field>
      </Section>

      <Section title="Your Identity">
        <Field label="Full Name">
          <Input value={form.user_name} onChange={v => setField('user_name', v)} placeholder="Your Full Name" />
        </Field>
        <Field label="Email Address">
          <Input type="email" value={form.user_email} onChange={v => setField('user_email', v)} placeholder="you@example.com" />
        </Field>
        <Field label="BCC Address" hint="Optional — a copy of each email sent will be BCC'd here.">
          <Input type="email" value={form.bcc_email} onChange={v => setField('bcc_email', v)} placeholder="optional" />
        </Field>
      </Section>

      <div className="flex">
        <button
          onClick={handleSave}
          disabled={saving}
          className="px-6 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
        {saved && <span className="ml-3 self-center text-sm text-green-600 font-medium">✓ Saved</span>}
      </div>

      <Section title="Documents">
        <Field
          label="CV (DOCX)"
          hint={cfg.cv_exists ? '✓ File found (configured in config.py)' : '⚠ File not found — check CV_FILE in config.py'}
        >
          <div className="flex gap-3 items-center">
            <input ref={cvRef} type="file" accept=".docx" className="text-sm text-gray-500
              file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-gray-300
              file:text-sm file:font-medium file:bg-white file:text-gray-700
              hover:file:bg-gray-50 cursor-pointer" />
            <button
              onClick={() => uploadFile(cvRef, api.uploadCV, 'cv')}
              className="px-3 py-1.5 bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-200"
            >
              Upload
            </button>
            {uploadStatus.cv && (
              <span className={`text-xs ${uploadStatus.cv === 'done' ? 'text-green-600' : uploadStatus.cv === 'uploading' ? 'text-gray-500' : 'text-red-600'}`}>
                {uploadStatus.cv === 'done' ? '✓ Uploaded' : uploadStatus.cv === 'uploading' ? 'Uploading...' : uploadStatus.cv}
              </span>
            )}
          </div>
        </Field>

        <Field
          label="Data Lake (Markdown)"
          hint={cfg.data_lake_exists ? '✓ File found (configured in config.py)' : '⚠ File not found — check DATA_LAKE_FILE in config.py'}
        >
          <div className="flex gap-3 items-center">
            <input ref={dlRef} type="file" accept=".md,.txt" className="text-sm text-gray-500
              file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border file:border-gray-300
              file:text-sm file:font-medium file:bg-white file:text-gray-700
              hover:file:bg-gray-50 cursor-pointer" />
            <button
              onClick={() => uploadFile(dlRef, api.uploadDataLake, 'dl')}
              className="px-3 py-1.5 bg-gray-100 border border-gray-300 rounded-lg text-sm font-medium hover:bg-gray-200"
            >
              Upload
            </button>
            {uploadStatus.dl && (
              <span className={`text-xs ${uploadStatus.dl === 'done' ? 'text-green-600' : uploadStatus.dl === 'uploading' ? 'text-gray-500' : 'text-red-600'}`}>
                {uploadStatus.dl === 'done' ? '✓ Uploaded' : uploadStatus.dl === 'uploading' ? 'Uploading...' : uploadStatus.dl}
              </span>
            )}
          </div>
        </Field>
      </Section>
    </div>
  )
}
