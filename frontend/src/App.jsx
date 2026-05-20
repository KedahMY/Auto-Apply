import { useEffect, useRef } from 'react'
import { NavLink, Route, Routes, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Scrape from './pages/Scrape'
import Jobs from './pages/Jobs'
import Settings from './pages/Settings'

function useScrollToTop(ref) {
  const { pathname } = useLocation()
  useEffect(() => { ref.current?.scrollTo(0, 0) }, [pathname])
}

const nav = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/scrape', label: 'Scrape', icon: '🔍' },
  { to: '/jobs', label: 'Jobs', icon: '💼' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
]

export default function App() {
  const mainRef = useRef(null)
  useScrollToTop(mainRef)

  return (
    <div className="flex h-screen overflow-hidden">
      <aside className="w-52 bg-gray-900 text-white flex flex-col flex-shrink-0">
        <div className="px-5 py-4 border-b border-gray-700">
          <h1 className="text-lg font-bold tracking-tight">Auto-Apply</h1>
          <p className="text-xs text-gray-400 mt-0.5">HKUST Career Portal</p>
        </div>
        <nav className="flex-1 px-3 py-4 space-y-1">
          {nav.map(({ to, label, icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <span>{icon}</span>
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main ref={mainRef} className="flex-1 overflow-y-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/scrape" element={<Scrape />} />
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}
