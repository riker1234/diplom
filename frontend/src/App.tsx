import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import HomePage from './pages/HomePage'
import QuizPage from './pages/QuizPage'
import ResultsPage from './pages/ResultsPage'
import CatalogPage from './pages/CatalogPage'
import SetupPage from './pages/SetupPage'

function useTheme() {
  const [dark, setDark] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved) return saved === 'dark'
    return window.matchMedia('(prefers-color-scheme: dark)').matches
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
  }, [dark])

  return { dark, toggle: () => setDark(d => !d) }
}

function Navbar() {
  const location = useLocation()
  const { dark, toggle } = useTheme()

  const linkClass = (path: string) =>
    `text-sm transition-colors ${
      location.pathname === path
        ? 'text-blue-600 font-medium'
        : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
    }`

  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="font-semibold text-gray-900 dark:text-white text-base tracking-tight">
          ПериферияПодбор
        </Link>
        <div className="flex items-center gap-6">
          <Link to="/" className={linkClass('/')}>Подбор</Link>
          <Link to="/setup" className={linkClass('/setup')}>Комплект</Link>
          <Link to="/catalog" className={linkClass('/catalog')}>Каталог</Link>
          <button
            onClick={toggle}
            className="w-8 h-8 rounded-full flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label="Переключить тему"
          >
            {dark ? '☀️' : '🌙'}
          </button>
        </div>
      </div>
    </nav>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      <Navbar />
      {children}
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/quiz/:category" element={<QuizPage />} />
          <Route path="/results" element={<ResultsPage />} />
          <Route path="/catalog" element={<CatalogPage />} />
          <Route path="/setup" element={<SetupPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
