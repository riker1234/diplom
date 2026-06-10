import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { SunIcon, MoonIcon } from './components/icons'
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
  const [menuOpen, setMenuOpen] = useState(false)

  // Закрываем мобильное меню при переходе на другую страницу
  useEffect(() => {
    setMenuOpen(false)
  }, [location.pathname])

  const linkClass = (path: string) =>
    `text-sm transition-colors ${
      location.pathname === path
        ? 'text-blue-600 font-medium'
        : 'text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white'
    }`

  const themeButton = (
    <button
      onClick={toggle}
      className="w-8 h-8 rounded-full flex items-center justify-center text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      aria-label="Переключить тему"
    >
      {dark ? <SunIcon className="w-5 h-5" /> : <MoonIcon className="w-5 h-5" />}
    </button>
  )

  return (
    <nav className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="font-semibold text-gray-900 dark:text-white text-base tracking-tight">
          ПериферияПодбор
        </Link>

        {/* Десктоп: меню в ряд (как было) */}
        <div className="hidden md:flex items-center gap-6">
          <Link to="/" className={linkClass('/')}>Подбор</Link>
          <Link to="/setup" className={linkClass('/setup')}>Комплект</Link>
          <Link to="/catalog" className={linkClass('/catalog')}>Каталог</Link>
          {themeButton}
        </div>

        {/* Мобильный: тема + бургер */}
        <div className="flex md:hidden items-center gap-1">
          {themeButton}
          <button
            onClick={() => setMenuOpen((o) => !o)}
            className="w-9 h-9 rounded-lg flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            aria-label={menuOpen ? 'Закрыть меню' : 'Открыть меню'}
          >
            <svg viewBox="0 0 24 24" className="w-6 h-6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              {menuOpen
                ? <><line x1="6" y1="6" x2="18" y2="18" /><line x1="18" y1="6" x2="6" y2="18" /></>
                : <><line x1="4" y1="7" x2="20" y2="7" /><line x1="4" y1="12" x2="20" y2="12" /><line x1="4" y1="17" x2="20" y2="17" /></>}
            </svg>
          </button>
        </div>
      </div>

      {/* Мобильное выпадающее меню */}
      {menuOpen && (
        <div className="md:hidden border-t border-gray-100 dark:border-gray-800 px-4 py-2 flex flex-col bg-white dark:bg-gray-900">
          <Link to="/" className={`${linkClass('/')} py-2.5`}>Подбор</Link>
          <Link to="/setup" className={`${linkClass('/setup')} py-2.5`}>Комплект</Link>
          <Link to="/catalog" className={`${linkClass('/catalog')} py-2.5`}>Каталог</Link>
        </div>
      )}
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
