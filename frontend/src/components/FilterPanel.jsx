const FILTER_GROUPS = [
  { label: 'Business Nature', param: 'BN[]', options: {
    'Accounting': '1', 'Advertising / Marketing / PR': '2', 'Aviation / Transport / Logistics': '3',
    'Banking/Finance - Commercial Banks': '5', 'Banking/Finance - Investment Banks': '40',
    'Banking/Finance - Other Financial': '7', 'Banking/Finance - PE / Hedge / Asset Mgmt': '6',
    'Beauty / Health Care / Fitness': '8', 'Biotechnology / Chemicals / Lab': '9',
    'Catering / Food & Beverage': '10', 'Charity / NGO / Quasi-gov': '11',
    'Civil Service / Government': '54', 'Construction / Architecture / Surveying': '4',
    'Education / Research / Training': '14', 'Engineering / Technical Services': '15',
    'Environmental Science': '16', 'FMCG': '17', 'General Business / Consulting': '18',
    'HKUST': '52', 'Hospitality / Hotels / Tourism': '20', 'HR / Recruitment': '19',
    'Information Technology / FinTech': '21', 'Insurance': '22',
    'Internet / Digital / e-Commerce': '23', 'Internship Program Organizers': '53',
    'Legal Services': '24', 'Management Consulting': '26', 'Manufacturing': '25',
    'Media / Publishing': '27', 'Medical / Pharmaceutical': '28', 'Motor Vehicles': '29',
    'Multi-nature Conglomerates': '30', 'Others': '35',
    'Property / Real Estate': '31', 'Retail / Trading / Import & Export': '32',
    'Telecommunication': '33', 'Utilities / Energy / Power': '34',
  }},
  { label: 'Job Nature', param: 'JN[]', options: {
    'Accounting / Auditing / Tax': '1', 'Administration (Non-private)': '2',
    'Administration (Private)': '3', 'Architecture / Interior Design': '4',
    'Banking and Finance Executive': '5', 'Civil Service / Government': '33',
    'Community / Social Worker': '6', 'Creative / Design / Artist': '7',
    'Customer Services': '8', 'Disciplinary Forces': '9',
    'Engineering (Biological/Chemical/Electronic/Mechanical)': '11',
    'Engineering (Construction / Building)': '10', 'HR / Training / Recruitment': '12',
    'IT / Programming': '13', 'Journalist / Editor / Translation': '14',
    'Legal / Compliance': '15', 'Library Officer': '16', 'Logistics / Supply Chain': '17',
    'Management Consultant / Business Analyst': '18', 'Management Trainee': '19',
    'Marketing / Market Research': '20', 'Medical / Therapist / Pharmacist': '21',
    'Merchandising / Buying': '22', 'Miscellaneous': '23', 'Others': '31',
    'PR / Event Management': '24', 'Quality Control': '25',
    'Research & Development': '26', 'Research Assistant / Technician': '27',
    'Sales / Business Development': '28', 'Surveying': '29', 'Teaching': '30',
  }},
  { label: 'Employment Type', param: 'EMT[]', options: {
    'ASEAN Internship': '6', 'Co-op': '13', 'Government Summer Job (PSSSIP)': '8',
    'Graduate Job': '3', 'Internship (above minimum wage)': '14',
    'Internship (below minimum wage)': '15', 'On-Campus Internship': '9',
    'STEM Internship': '11', 'Unpaid Work': '16', 'Volunteer Work': '17',
    'UPOP Internship': '12', 'Others': '5',
  }},
  { label: 'Working Location', param: 'WL[]', options: {
    'Hong Kong': '1', 'Macau': '2', 'Singapore': '3', 'Chinese Mainland': '4',
    'Malaysia': '9', 'Virtual': '22', 'Various Locations': '15', 'Japan': '14',
    'USA': '17', 'Korea': '20', 'Thailand': '11', 'Philippines': '12',
    'Vietnam': '13', 'Indonesia': '7', 'Brunei Darussalam': '5',
    'Cambodia': '6', 'Laos': '8', 'Myanmar': '18', 'Taiwan, China': '23',
    'Switzerland': '21', 'Europe': '16', 'Belt and Road Countries': '24', 'Others': '19',
  }},
  { label: 'Qualification', param: 'awards[]', options: {
    'Undergraduate': 'bachelor', 'Taught Postgraduate': 'master', 'Research Postgraduate': 'phd',
  }},
  { label: 'Employment Mode', param: 'EM[]', options: {
    'Full Time': 'FT', 'Part Time': 'PT',
  }},
  { label: 'Language', param: 'L[]', options: {
    'English (Writing)': 'wen', 'English (Speaking)': 'sen',
    'Chinese (Writing)': 'zh', 'Cantonese (Speaking)': 'zh-hk',
    'Putonghua (Speaking)': 'zh-cn', 'Others': 'other',
  }},
]

export default function FilterPanel({ filters, onChange }) {
  function setMulti(param, value, checked) {
    const current = filters[param] || []
    const next = checked
      ? [...current, value]
      : current.filter(v => v !== value)
    onChange({ ...filters, [param]: next })
  }

  function setScalar(key, value) {
    onChange({ ...filters, [key]: value })
  }

  function setFlag(key, checked) {
    const next = { ...filters }
    if (checked) next[key] = true
    else delete next[key]
    onChange(next)
  }

  return (
    <div className="space-y-5">
      {FILTER_GROUPS.map(({ label, param, options }) => (
        <div key={param}>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">{label}</h3>
          <div className="space-y-1 max-h-36 overflow-y-auto pr-1">
            {Object.entries(options).map(([name, val]) => (
              <label key={val} className="flex items-center gap-2 text-sm cursor-pointer hover:text-blue-600">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-blue-600"
                  checked={(filters[param] || []).includes(val)}
                  onChange={e => setMulti(param, val, e.target.checked)}
                />
                {name}
              </label>
            ))}
          </div>
        </div>
      ))}

      <div>
        <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Keyword</h3>
        <input
          type="text"
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          placeholder="e.g. software engineer"
          value={filters.keywords || ''}
          onChange={e => setScalar('keywords', e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" className="rounded border-gray-300 text-blue-600"
            checked={!!filters.AJOB} onChange={e => setFlag('AJOB', e.target.checked)} />
          Active jobs only
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" className="rounded border-gray-300 text-blue-600"
            checked={!!filters.NCHI} onChange={e => setFlag('NCHI', e.target.checked)} />
          Non-Chinese speaking students considered
        </label>
      </div>
    </div>
  )
}
