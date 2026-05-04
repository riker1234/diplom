# СППР Периферия — Plan 2: React Frontend

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Построить React фронтенд с выбором категории периферии, пошаговым опросником, отображением рекомендованных товаров и поиском магазинов DNS по городу.

**Architecture:** Vite + React SPA с React Router для навигации; Axios для запросов к FastAPI бэкенду; компоненты разделены по ответственности — страницы (pages) оркестрируют данные, компоненты (components) только отображают.

**Tech Stack:** Node.js 20+, React 18, Vite 5, React Router 6, Axios, CSS Modules (встроен в Vite, не требует настройки)

**Требование:** Бэкенд из Plan 1 должен быть запущен (`uvicorn app.main:app --reload`) перед тестированием фронтенда.

---

## Структура файлов

```
frontend/
├── public/
├── src/
│   ├── main.jsx                       # Точка входа, BrowserRouter
│   ├── App.jsx                        # Роуты приложения
│   ├── api/
│   │   └── client.js                  # Axios инстанс + все API-функции
│   ├── pages/
│   │   ├── HomePage.jsx               # Список категорий
│   │   ├── QuestionnairePage.jsx      # Опросник для категории
│   │   ├── ResultsPage.jsx            # Список рекомендованных товаров
│   │   └── ProductPage.jsx            # Детальная страница товара + магазины
│   ├── components/
│   │   ├── CategoryCard.jsx           # Карточка категории на главной
│   │   ├── QuestionStep.jsx           # Один вопрос опросника
│   │   ├── ProgressBar.jsx            # Прогресс опросника
│   │   ├── ProductCard.jsx            # Карточка товара в результатах
│   │   ├── StoreLocator.jsx           # Поиск магазинов по городу
│   │   └── Navbar.jsx                 # Верхняя навигация
│   └── styles/
│       └── global.css                 # Базовые стили
├── package.json
└── vite.config.js
```

---

## Task 1: Настройка React проекта

**Files:**
- Create: `frontend/` (весь каталог через Vite)
- Create: `frontend/vite.config.js`
- Create: `frontend/src/api/client.js`

- [ ] **Step 1: Создать React проект через Vite**

```powershell
cd c:\Users\User\Desktop\diplom
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom axios
```

- [ ] **Step 2: Проверить что проект запускается**

```powershell
npm run dev
```

Открыть `http://localhost:5173` — должна открыться дефолтная страница Vite + React.
Остановить сервер: `Ctrl+C`

- [ ] **Step 3: Очистить шаблонный код — заменить src/App.jsx**

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import QuestionnairePage from './pages/QuestionnairePage'
import ResultsPage from './pages/ResultsPage'
import ProductPage from './pages/ProductPage'
import './styles/global.css'

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <main style={{ maxWidth: 1100, margin: '0 auto', padding: '0 16px' }}>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/category/:category" element={<QuestionnairePage />} />
          <Route path="/results/:category" element={<ResultsPage />} />
          <Route path="/product/:category/:id" element={<ProductPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
```

- [ ] **Step 4: Создать src/main.jsx (заменить содержимое)**

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

- [ ] **Step 5: Создать src/styles/global.css**

```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #1a1a1a;
  line-height: 1.5;
}

a {
  color: #2563eb;
  text-decoration: none;
}

button {
  cursor: pointer;
}
```

- [ ] **Step 6: Создать src/api/client.js**

```js
import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10000,
})

export const getQuestions = (category) =>
  api.get(`/recommend/questions/${category}`).then((r) => r.data)

export const getRecommendations = (category, answers) =>
  api.post('/recommend/', { category, answers }).then((r) => r.data)

export const getProduct = (category, id) => {
  const endpoints = {
    mouse: `/mice/${id}`,
    keyboard: `/keyboards/${id}`,
    mousepad: `/mousepads/${id}`,
    monitor: `/monitors/${id}`,
    microphone: `/microphones/${id}`,
    headphones: `/headphones/${id}`,
  }
  return api.get(endpoints[category]).then((r) => r.data)
}

export const getStoreAvailability = (productType, productId, city) =>
  api
    .get('/stores/availability', { params: { product_type: productType, product_id: productId, city } })
    .then((r) => r.data)

export const triggerDataUpdate = () =>
  api.post('/admin/update-data').then((r) => r.data)
```

- [ ] **Step 7: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/
git commit -m "feat: scaffold React frontend with Vite and routing"
```

---

## Task 2: Navbar и заглушки для страниц

**Files:**
- Create: `frontend/src/components/Navbar.jsx`
- Create: `frontend/src/pages/HomePage.jsx` (stub)
- Create: `frontend/src/pages/QuestionnairePage.jsx` (stub)
- Create: `frontend/src/pages/ResultsPage.jsx` (stub)
- Create: `frontend/src/pages/ProductPage.jsx` (stub)

- [ ] **Step 1: Создать components/Navbar.jsx**

```jsx
import { Link } from 'react-router-dom'

const styles = {
  nav: {
    background: '#1e3a5f',
    padding: '12px 24px',
    display: 'flex',
    alignItems: 'center',
    gap: 24,
    marginBottom: 32,
  },
  logo: { color: '#fff', fontWeight: 700, fontSize: 20 },
  link: { color: '#cbd5e1', fontSize: 14 },
}

export default function Navbar() {
  return (
    <nav style={styles.nav}>
      <Link to="/" style={styles.logo}>ПК Периферия</Link>
      <Link to="/" style={styles.link}>Главная</Link>
    </nav>
  )
}
```

- [ ] **Step 2: Создать заглушки для страниц**

`frontend/src/pages/HomePage.jsx`:
```jsx
export default function HomePage() {
  return <h1>Главная — выбор категории</h1>
}
```

`frontend/src/pages/QuestionnairePage.jsx`:
```jsx
export default function QuestionnairePage() {
  return <h1>Опросник</h1>
}
```

`frontend/src/pages/ResultsPage.jsx`:
```jsx
export default function ResultsPage() {
  return <h1>Результаты</h1>
}
```

`frontend/src/pages/ProductPage.jsx`:
```jsx
export default function ProductPage() {
  return <h1>Товар</h1>
}
```

- [ ] **Step 3: Запустить и проверить навигацию**

```powershell
cd c:\Users\User\Desktop\diplom\frontend
npm run dev
```

Открыть `http://localhost:5173` — должны видеть navbar и заголовок "Главная — выбор категории".
Проверить переход `/category/mouse` — заголовок "Опросник".

- [ ] **Step 4: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/src/
git commit -m "feat: add navbar and page stubs"
```

---

## Task 3: Главная страница — выбор категории

**Files:**
- Modify: `frontend/src/pages/HomePage.jsx`
- Create: `frontend/src/components/CategoryCard.jsx`

- [ ] **Step 1: Создать components/CategoryCard.jsx**

```jsx
import { useNavigate } from 'react-router-dom'

const styles = {
  card: {
    background: '#fff',
    borderRadius: 12,
    padding: 24,
    cursor: 'pointer',
    border: '2px solid transparent',
    transition: 'border-color 0.2s, box-shadow 0.2s',
    textAlign: 'center',
    userSelect: 'none',
  },
  emoji: { fontSize: 48, display: 'block', marginBottom: 12 },
  title: { fontSize: 18, fontWeight: 600, color: '#1a1a1a' },
  subtitle: { fontSize: 13, color: '#6b7280', marginTop: 4 },
}

export default function CategoryCard({ category, emoji, title, subtitle }) {
  const navigate = useNavigate()

  return (
    <div
      style={styles.card}
      onClick={() => navigate(`/category/${category}`)}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = '#2563eb'
        e.currentTarget.style.boxShadow = '0 4px 16px rgba(37,99,235,0.15)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'transparent'
        e.currentTarget.style.boxShadow = 'none'
      }}
    >
      <span style={styles.emoji}>{emoji}</span>
      <div style={styles.title}>{title}</div>
      {subtitle && <div style={styles.subtitle}>{subtitle}</div>}
    </div>
  )
}
```

- [ ] **Step 2: Обновить pages/HomePage.jsx**

```jsx
import CategoryCard from '../components/CategoryCard'

const CATEGORIES = [
  { category: 'mouse',       emoji: '🖱️',  title: 'Мышки',      subtitle: 'Игровые и офисные' },
  { category: 'keyboard',    emoji: '⌨️',  title: 'Клавиатуры', subtitle: 'Механические и мембранные' },
  { category: 'mousepad',    emoji: '🟫',  title: 'Коврики',    subtitle: 'Для мышки' },
  { category: 'monitor',     emoji: '🖥️',  title: 'Мониторы',   subtitle: 'Игровые и рабочие' },
  { category: 'microphone',  emoji: '🎙️',  title: 'Микрофоны',  subtitle: 'USB и XLR' },
  { category: 'headphones',  emoji: '🎧',  title: 'Наушники',   subtitle: 'С ANC и без' },
]

const styles = {
  header: { marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 700 },
  subtitle: { color: '#6b7280', marginTop: 8 },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
    gap: 20,
  },
}

export default function HomePage() {
  return (
    <div>
      <div style={styles.header}>
        <h1 style={styles.title}>Подбор периферии для ПК</h1>
        <p style={styles.subtitle}>Выберите категорию — мы зададим несколько вопросов и подберём лучшие варианты</p>
      </div>
      <div style={styles.grid}>
        {CATEGORIES.map((cat) => (
          <CategoryCard key={cat.category} {...cat} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Проверить главную страницу**

Открыть `http://localhost:5173` — должна отображаться сетка из 6 карточек.
Кликнуть на любую карточку — должен произойти переход на `/category/{category}`.

- [ ] **Step 4: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/src/
git commit -m "feat: add home page with category selection grid"
```

---

## Task 4: Страница опросника

**Files:**
- Create: `frontend/src/components/QuestionStep.jsx`
- Create: `frontend/src/components/ProgressBar.jsx`
- Modify: `frontend/src/pages/QuestionnairePage.jsx`

- [ ] **Step 1: Создать components/ProgressBar.jsx**

```jsx
export default function ProgressBar({ current, total }) {
  const percent = Math.round((current / total) * 100)
  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: 13, color: '#6b7280' }}>
        <span>Вопрос {current} из {total}</span>
        <span>{percent}%</span>
      </div>
      <div style={{ height: 6, background: '#e5e7eb', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${percent}%`, background: '#2563eb', borderRadius: 4, transition: 'width 0.3s' }} />
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Создать components/QuestionStep.jsx**

```jsx
const styles = {
  question: { fontSize: 22, fontWeight: 600, marginBottom: 24 },
  options: { display: 'flex', flexDirection: 'column', gap: 12 },
  option: {
    padding: '14px 20px',
    border: '2px solid #e5e7eb',
    borderRadius: 10,
    background: '#fff',
    fontSize: 16,
    textAlign: 'left',
    transition: 'border-color 0.15s, background 0.15s',
  },
  optionSelected: {
    borderColor: '#2563eb',
    background: '#eff6ff',
  },
}

export default function QuestionStep({ question, selectedValue, onSelect }) {
  return (
    <div>
      <p style={styles.question}>{question.text}</p>
      <div style={styles.options}>
        {question.options.map((opt) => (
          <button
            key={opt.value}
            style={{
              ...styles.option,
              ...(selectedValue === opt.value ? styles.optionSelected : {}),
            }}
            onClick={() => onSelect(opt.value)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Обновить pages/QuestionnairePage.jsx**

```jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getQuestions } from '../api/client'
import QuestionStep from '../components/QuestionStep'
import ProgressBar from '../components/ProgressBar'

const CATEGORY_LABELS = {
  mouse: 'Мышка', keyboard: 'Клавиатура', mousepad: 'Коврик',
  monitor: 'Монитор', microphone: 'Микрофон', headphones: 'Наушники',
}

const styles = {
  container: { maxWidth: 600, margin: '0 auto' },
  header: { marginBottom: 32 },
  title: { fontSize: 26, fontWeight: 700 },
  subtitle: { color: '#6b7280', marginTop: 6 },
  card: { background: '#fff', borderRadius: 14, padding: 32, boxShadow: '0 2px 12px rgba(0,0,0,0.07)' },
  nav: { display: 'flex', justifyContent: 'space-between', marginTop: 32 },
  btnBack: { padding: '12px 24px', border: '1px solid #d1d5db', borderRadius: 8, background: '#fff', fontSize: 15 },
  btnNext: { padding: '12px 28px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 600 },
  btnNextDisabled: { opacity: 0.4, cursor: 'default' },
}

export default function QuestionnairePage() {
  const { category } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState([])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getQuestions(category)
      .then(setQuestions)
      .catch(() => setError('Не удалось загрузить вопросы. Убедитесь что бэкенд запущен.'))
      .finally(() => setLoading(false))
  }, [category])

  if (loading) return <p style={{ textAlign: 'center', marginTop: 64 }}>Загрузка...</p>
  if (error) return <p style={{ color: 'red', textAlign: 'center', marginTop: 64 }}>{error}</p>

  const currentQuestion = questions[step]
  const currentAnswer = answers[currentQuestion?.id]
  const isLast = step === questions.length - 1

  const handleNext = () => {
    if (isLast) {
      navigate(`/results/${category}`, { state: { answers } })
    } else {
      setStep((s) => s + 1)
    }
  }

  const handleBack = () => {
    if (step === 0) navigate('/')
    else setStep((s) => s - 1)
  }

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.title}>Подбор: {CATEGORY_LABELS[category] || category}</h1>
        <p style={styles.subtitle}>Ответьте на несколько вопросов для подбора</p>
      </div>
      <div style={styles.card}>
        <ProgressBar current={step + 1} total={questions.length} />
        {currentQuestion && (
          <QuestionStep
            question={currentQuestion}
            selectedValue={currentAnswer}
            onSelect={(value) => setAnswers((prev) => ({ ...prev, [currentQuestion.id]: value }))}
          />
        )}
        <div style={styles.nav}>
          <button style={styles.btnBack} onClick={handleBack}>← Назад</button>
          <button
            style={{ ...styles.btnNext, ...(!currentAnswer ? styles.btnNextDisabled : {}) }}
            onClick={handleNext}
            disabled={!currentAnswer}
          >
            {isLast ? 'Показать результаты' : 'Далее →'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Проверить опросник**

1. Открыть `http://localhost:5173`
2. Нажать на "Мышки"
3. Убедиться что вопросы загружаются (бэкенд должен быть запущен)
4. Отвечать на вопросы, проверить прогресс-бар
5. На последнем вопросе нажать "Показать результаты"

- [ ] **Step 5: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/src/
git commit -m "feat: add questionnaire flow with step-by-step questions and progress"
```

---

## Task 5: Страница результатов

**Files:**
- Create: `frontend/src/components/ProductCard.jsx`
- Modify: `frontend/src/pages/ResultsPage.jsx`

- [ ] **Step 1: Создать components/ProductCard.jsx**

```jsx
import { useNavigate } from 'react-router-dom'

const styles = {
  card: {
    background: '#fff',
    borderRadius: 12,
    overflow: 'hidden',
    boxShadow: '0 2px 8px rgba(0,0,0,0.07)',
    transition: 'box-shadow 0.2s',
    cursor: 'pointer',
  },
  image: { width: '100%', height: 180, objectFit: 'contain', background: '#f9fafb', padding: 12 },
  imagePlaceholder: {
    width: '100%', height: 180, background: '#f1f5f9',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    fontSize: 48,
  },
  body: { padding: 16 },
  name: { fontSize: 15, fontWeight: 600, marginBottom: 4, lineHeight: 1.4 },
  price: { fontSize: 20, fontWeight: 700, color: '#2563eb', marginBottom: 12 },
  links: { display: 'flex', gap: 8, flexWrap: 'wrap' },
  linkBtn: {
    padding: '6px 12px', borderRadius: 6, fontSize: 13, border: 'none',
    cursor: 'pointer', textDecoration: 'none', display: 'inline-block',
  },
}

const EMOJI_MAP = {
  mouse: '🖱️', keyboard: '⌨️', mousepad: '🟫',
  monitor: '🖥️', microphone: '🎙️', headphones: '🎧',
}

export default function ProductCard({ product, category }) {
  const navigate = useNavigate()

  const formatPrice = (price) =>
    price ? `${Math.round(price).toLocaleString('ru-RU')} ₽` : 'Цена не указана'

  return (
    <div
      style={styles.card}
      onClick={() => navigate(`/product/${category}/${product.id}`)}
      onMouseEnter={(e) => (e.currentTarget.style.boxShadow = '0 6px 20px rgba(0,0,0,0.12)')}
      onMouseLeave={(e) => (e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.07)')}
    >
      {product.image_url ? (
        <img src={product.image_url} alt={product.name} style={styles.image} />
      ) : (
        <div style={styles.imagePlaceholder}>{EMOJI_MAP[category] || '📦'}</div>
      )}
      <div style={styles.body}>
        <div style={styles.name}>{product.name}</div>
        <div style={styles.price}>{formatPrice(product.price)}</div>
        <div style={styles.links} onClick={(e) => e.stopPropagation()}>
          {product.dns_url && (
            <a href={product.dns_url} target="_blank" rel="noopener noreferrer"
              style={{ ...styles.linkBtn, background: '#ef4444', color: '#fff' }}>
              DNS
            </a>
          )}
          {product.wb_url && (
            <a href={product.wb_url} target="_blank" rel="noopener noreferrer"
              style={{ ...styles.linkBtn, background: '#7c3aed', color: '#fff' }}>
              Wildberries
            </a>
          )}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Обновить pages/ResultsPage.jsx**

```jsx
import { useState, useEffect } from 'react'
import { useParams, useLocation, useNavigate } from 'react-router-dom'
import { getRecommendations } from '../api/client'
import ProductCard from '../components/ProductCard'

const CATEGORY_LABELS = {
  mouse: 'Мышки', keyboard: 'Клавиатуры', mousepad: 'Коврики',
  monitor: 'Мониторы', microphone: 'Микрофоны', headphones: 'Наушники',
}

const styles = {
  header: { display: 'flex', alignItems: 'center', gap: 16, marginBottom: 28 },
  title: { fontSize: 24, fontWeight: 700 },
  count: { color: '#6b7280', fontSize: 15 },
  btnBack: { padding: '10px 20px', border: '1px solid #d1d5db', borderRadius: 8, background: '#fff' },
  btnRetake: { padding: '10px 20px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(240px, 1fr))', gap: 20 },
  empty: { textAlign: 'center', padding: 64, color: '#6b7280', fontSize: 18 },
}

export default function ResultsPage() {
  const { category } = useParams()
  const { state } = useLocation()
  const navigate = useNavigate()
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!state?.answers) {
      navigate(`/category/${category}`)
      return
    }
    getRecommendations(category, state.answers)
      .then(setProducts)
      .catch(() => setError('Не удалось загрузить результаты'))
      .finally(() => setLoading(false))
  }, [category, state, navigate])

  if (loading) return <p style={{ textAlign: 'center', marginTop: 64 }}>Подбираем варианты...</p>
  if (error) return <p style={{ color: 'red', textAlign: 'center', marginTop: 64 }}>{error}</p>

  return (
    <div>
      <div style={styles.header}>
        <div style={{ flex: 1 }}>
          <h1 style={styles.title}>Рекомендации: {CATEGORY_LABELS[category] || category}</h1>
          <p style={styles.count}>{products.length > 0 ? `Найдено ${products.length} вариантов` : 'Ничего не найдено'}</p>
        </div>
        <button style={styles.btnBack} onClick={() => navigate('/')}>На главную</button>
        <button style={styles.btnRetake} onClick={() => navigate(`/category/${category}`)}>Пройти снова</button>
      </div>

      {products.length === 0 ? (
        <div style={styles.empty}>
          Ничего не нашлось по вашим параметрам.<br />
          Попробуйте изменить ответы или обновить базу данных.
        </div>
      ) : (
        <div style={styles.grid}>
          {products.map((p) => (
            <ProductCard key={p.id} product={p} category={category} />
          ))}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: Проверить результаты**

1. Пройти опросник для любой категории
2. Убедиться что товары отображаются (нужны данные в БД — запустить `POST /admin/update-data`)
3. Проверить что клик по карточке ведёт на `/product/{category}/{id}`
4. Проверить ссылки DNS / WB открываются в новой вкладке

- [ ] **Step 4: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/src/
git commit -m "feat: add results page with product cards grid"
```

---

## Task 6: Страница товара и Store Locator

**Files:**
- Create: `frontend/src/components/StoreLocator.jsx`
- Modify: `frontend/src/pages/ProductPage.jsx`

- [ ] **Step 1: Создать components/StoreLocator.jsx**

```jsx
import { useState } from 'react'
import { getStoreAvailability } from '../api/client'

const styles = {
  section: { marginTop: 32, padding: 24, background: '#fff', borderRadius: 12, boxShadow: '0 2px 8px rgba(0,0,0,0.07)' },
  title: { fontSize: 18, fontWeight: 700, marginBottom: 16 },
  row: { display: 'flex', gap: 12, marginBottom: 16 },
  input: { flex: 1, padding: '10px 14px', border: '1px solid #d1d5db', borderRadius: 8, fontSize: 15 },
  btn: { padding: '10px 20px', background: '#2563eb', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 600 },
  store: { padding: '12px 0', borderBottom: '1px solid #f1f5f9' },
  storeName: { fontWeight: 600, marginBottom: 2 },
  storeAddress: { color: '#374151', fontSize: 15 },
  badge: { display: 'inline-block', padding: '2px 10px', borderRadius: 12, fontSize: 12, fontWeight: 600, marginTop: 4 },
  badgeIn: { background: '#d1fae5', color: '#065f46' },
  badgeOut: { background: '#fee2e2', color: '#991b1b' },
  empty: { color: '#6b7280', textAlign: 'center', padding: 24 },
}

export default function StoreLocator({ category, productId }) {
  const [city, setCity] = useState('')
  const [stores, setStores] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = () => {
    if (!city.trim()) return
    setLoading(true)
    setError(null)
    getStoreAvailability(category, productId, city.trim())
      .then(setStores)
      .catch(() => setError('Не удалось получить данные о наличии'))
      .finally(() => setLoading(false))
  }

  return (
    <div style={styles.section}>
      <div style={styles.title}>Где купить в магазине DNS</div>
      <div style={styles.row}>
        <input
          style={styles.input}
          placeholder="Введите название города (напр. Москва)"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
        />
        <button style={styles.btn} onClick={handleSearch} disabled={loading}>
          {loading ? 'Поиск...' : 'Найти'}
        </button>
      </div>

      {error && <p style={{ color: 'red' }}>{error}</p>}

      {stores !== null && (
        stores.length === 0 ? (
          <div style={styles.empty}>Магазины DNS с этим товаром в городе «{city}» не найдены</div>
        ) : (
          stores.map((store, i) => (
            <div key={i} style={styles.store}>
              <div style={styles.storeName}>{store.store_name}</div>
              <div style={styles.storeAddress}>{store.store_address}</div>
              <span style={{ ...styles.badge, ...(store.in_stock ? styles.badgeIn : styles.badgeOut) }}>
                {store.in_stock ? 'В наличии' : 'Нет в наличии'}
              </span>
            </div>
          ))
        )
      )}
    </div>
  )
}
```

- [ ] **Step 2: Обновить pages/ProductPage.jsx**

```jsx
import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getProduct } from '../api/client'
import StoreLocator from '../components/StoreLocator'

const CATEGORY_LABELS = {
  mouse: 'Мышки', keyboard: 'Клавиатуры', mousepad: 'Коврики',
  monitor: 'Мониторы', microphone: 'Микрофоны', headphones: 'Наушники',
}

const SPEC_LABELS = {
  sensor: 'Сенсор', switches: 'Переключатели', weight_g: 'Вес (г)',
  connection_types: 'Подключение', board_material: 'Материал корпуса',
  form_factor: 'Форм-фактор', keycap_material: 'Материал кейкапов',
  keycap_manufacturing: 'Способ изготовления кейкапов',
  size: 'Размер', surface_material: 'Материал поверхности',
  hardness: 'Жёсткость', has_rgb: 'RGB-подсветка',
  diagonal_inch: 'Диагональ (дюймов)', resolution: 'Разрешение',
  refresh_rate_hz: 'Частота обновления (Гц)', matrix_type: 'Тип матрицы',
  mic_type: 'Тип микрофона', directionality: 'Направленность',
  frequency_range: 'Частотный диапазон', construction_type: 'Конструкция',
  has_microphone: 'Встроенный микрофон', noise_cancellation: 'Шумоподавление',
}

const styles = {
  back: { marginBottom: 24, padding: '8px 16px', border: '1px solid #d1d5db', borderRadius: 8, background: '#fff' },
  layout: { display: 'grid', gridTemplateColumns: '300px 1fr', gap: 32, alignItems: 'start' },
  image: { width: '100%', borderRadius: 12, background: '#f9fafb', padding: 16 },
  imagePlaceholder: { width: '100%', height: 260, background: '#f1f5f9', borderRadius: 12, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 80 },
  name: { fontSize: 24, fontWeight: 700, marginBottom: 8 },
  price: { fontSize: 30, fontWeight: 700, color: '#2563eb', marginBottom: 20 },
  specs: { background: '#fff', borderRadius: 12, padding: 20, boxShadow: '0 2px 8px rgba(0,0,0,0.07)', marginBottom: 16 },
  specsTitle: { fontWeight: 700, marginBottom: 12, fontSize: 16 },
  row: { display: 'flex', gap: 8, padding: '8px 0', borderBottom: '1px solid #f1f5f9', fontSize: 14 },
  label: { color: '#6b7280', minWidth: 200 },
  value: { fontWeight: 500 },
  links: { display: 'flex', gap: 12 },
  link: { padding: '12px 24px', borderRadius: 8, fontWeight: 600, fontSize: 15 },
}

const EMOJI_MAP = { mouse: '🖱️', keyboard: '⌨️', mousepad: '🟫', monitor: '🖥️', microphone: '🎙️', headphones: '🎧' }

const SKIP_FIELDS = new Set(['id', 'name', 'brand', 'price', 'image_url', 'dns_url', 'wb_url', 'dns_product_id', 'wb_sku', 'updated_at'])

export default function ProductPage() {
  const { category, id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProduct(category, id)
      .then(setProduct)
      .catch(() => setError('Товар не найден'))
      .finally(() => setLoading(false))
  }, [category, id])

  if (loading) return <p style={{ textAlign: 'center', marginTop: 64 }}>Загрузка...</p>
  if (error || !product) return <p style={{ color: 'red', textAlign: 'center', marginTop: 64 }}>{error}</p>

  const specs = Object.entries(product).filter(
    ([k, v]) => !SKIP_FIELDS.has(k) && v !== null && v !== undefined
  )

  return (
    <div>
      <button style={styles.back} onClick={() => navigate(-1)}>← Назад</button>

      <div style={styles.layout}>
        <div>
          {product.image_url ? (
            <img src={product.image_url} alt={product.name} style={styles.image} />
          ) : (
            <div style={styles.imagePlaceholder}>{EMOJI_MAP[category] || '📦'}</div>
          )}
        </div>

        <div>
          {product.brand && <p style={{ color: '#6b7280', marginBottom: 4 }}>{product.brand}</p>}
          <h1 style={styles.name}>{product.name}</h1>
          <div style={styles.price}>
            {product.price ? `${Math.round(product.price).toLocaleString('ru-RU')} ₽` : 'Цена не указана'}
          </div>

          <div style={styles.links}>
            {product.dns_url && (
              <a href={product.dns_url} target="_blank" rel="noopener noreferrer"
                style={{ ...styles.link, background: '#ef4444', color: '#fff' }}>
                Купить на DNS
              </a>
            )}
            {product.wb_url && (
              <a href={product.wb_url} target="_blank" rel="noopener noreferrer"
                style={{ ...styles.link, background: '#7c3aed', color: '#fff' }}>
                Купить на WB
              </a>
            )}
          </div>

          {specs.length > 0 && (
            <div style={{ ...styles.specs, marginTop: 24 }}>
              <div style={styles.specsTitle}>Характеристики</div>
              {specs.map(([key, value]) => (
                <div key={key} style={styles.row}>
                  <span style={styles.label}>{SPEC_LABELS[key] || key}</span>
                  <span style={styles.value}>{typeof value === 'boolean' ? (value ? 'Да' : 'Нет') : value}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <StoreLocator category={category} productId={parseInt(id)} />
    </div>
  )
}
```

- [ ] **Step 3: Проверить детальную страницу и Store Locator**

1. Открыть любой товар из результатов
2. Убедиться что характеристики отображаются
3. Ввести название города в Store Locator и нажать "Найти"
4. Проверить что ссылки "Купить на DNS" / "Купить на WB" открываются

- [ ] **Step 4: Commit**

```powershell
cd c:\Users\User\Desktop\diplom
git add frontend/src/
git commit -m "feat: add product detail page with specs and DNS store locator"
```

---

## Task 7: GitHub — подключение удалённого репозитория

- [ ] **Step 1: Создать репозиторий на GitHub**

Открыть `https://github.com/new` и создать новый репозиторий:
- Repository name: `peripheral-dss` (или на своё усмотрение)
- Visibility: Public или Private
- Не добавлять README / .gitignore (уже есть локально)
- Нажать "Create repository"

- [ ] **Step 2: Создать .gitignore в корне проекта**

Создать `c:\Users\User\Desktop\diplom\.gitignore`:
```
# Python
backend/venv/
backend/__pycache__/
backend/**/__pycache__/
backend/*.pyc
backend/.env
backend/test.db
backend/test_api.db

# Node
frontend/node_modules/
frontend/dist/

# Прочее
*.log
.DS_Store
```

- [ ] **Step 3: Подключить удалённый репозиторий и запушить**

Заменить `YOUR_USERNAME` и `YOUR_REPO_NAME` на свои данные:
```powershell
cd c:\Users\User\Desktop\diplom
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git branch -M main
git push -u origin main
```

- [ ] **Step 4: Проверить что код появился на GitHub**

Открыть `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME` — должны видеть все файлы.

- [ ] **Step 5: Настроить автоматический push после каждого коммита (опционально)**

Все последующие коммиты пушить командой:
```powershell
git push
```

(после `git push -u origin main` флаг `-u` запомнит удалённую ветку, и просто `git push` будет работать)

---

## Итог Plan 2

После выполнения всех задач у вас будет:

- ✅ Главная страница с выбором категории (6 карточек)
- ✅ Пошаговый опросник с прогресс-баром
- ✅ Страница результатов с карточками товаров
- ✅ Детальная страница товара с характеристиками
- ✅ Store Locator — поиск магазинов DNS по городу
- ✅ Ссылки на покупку в DNS и Wildberries
- ✅ Код опубликован на GitHub

**Запуск всего проекта:**

Терминал 1 (бэкенд):
```powershell
cd c:\Users\User\Desktop\diplom\backend
venv\Scripts\activate
uvicorn app.main:app --reload
```

Терминал 2 (фронтенд):
```powershell
cd c:\Users\User\Desktop\diplom\frontend
npm run dev
```

Открыть `http://localhost:5173` — приложение готово.
