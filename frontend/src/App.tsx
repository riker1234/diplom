import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import HomePage from './pages/HomePage'
import QuizPage from './pages/QuizPage'
import ResultsPage from './pages/ResultsPage'
import CatalogPage from './pages/CatalogPage'

function Navbar() {
  const location = useLocation()
  const linkClass = (path: string) =>
    `text-sm transition-colors ${
      location.pathname === path
        ? 'text-blue-600 font-medium'
        : 'text-gray-500 hover:text-gray-900'
    }`

  return (
    <nav className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link to="/" className="font-semibold text-gray-900 text-base tracking-tight">
          ПериферияПодбор
        </Link>
        <div className="flex gap-6">
          <Link to="/" className={linkClass('/')}>Подбор</Link>
          <Link to="/catalog" className={linkClass('/catalog')}>Каталог</Link>
        </div>
      </div>
    </nav>
  )
}

function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50">
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
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
