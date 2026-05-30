import { useState } from 'react'
import { fetchSetupRecommendation } from '../api'
import type { SetupResult, SetupRequest } from '../api'
import ProductModal from '../components/ProductModal'

const USE_CASE_OPTIONS = [
  { value: 'gaming', label: 'Игры', desc: 'Акцент на монитор и периферию для геймеров' },
  { value: 'work',   label: 'Работа', desc: 'Акцент на монитор и клавиатуру для продуктивности' },
  { value: 'both',   label: 'Всё вместе', desc: 'Универсальный баланс для игр и работы' },
]

const PRIORITY_OPTIONS = [
  { value: 'budget',   label: 'Сэкономить', desc: 'Найти лучшее за минимальные деньги' },
  { value: 'balance',  label: 'Баланс', desc: 'Оптимальное соотношение цены и качества' },
  { value: 'flagship', label: 'Лучшее', desc: 'Топовые модели без компромиссов' },
]

const CATEGORY_LABELS: Record<string, string> = {
  monitor:    'Монитор',
  keyboard:   'Клавиатура',
  mouse:      'Мышь',
  headphones: 'Наушники',
  mousepad:   'Коврик',
}

function formatPrice(p: number | null | undefined) {
  if (p == null) return '—'
  return p.toLocaleString('ru-RU') + ' ₽'
}

export default function SetupPage() {
  const [budget, setBudget] = useState('')
  const [useCase, setUseCase] = useState<SetupRequest['use_case']>('gaming')
  const [priority, setPriority] = useState<SetupRequest['priority']>('balance')
  const [result, setResult] = useState<SetupResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selected, setSelected] = useState<any | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const b = parseFloat(budget)
    if (!b || b < 5000) {
      setError('Минимальный бюджет — 5 000 ₽')
      return
    }
    setError('')
    setLoading(true)
    try {
      const data = await fetchSetupRecommendation({ total_budget: b, use_case: useCase, priority })
      setResult(data)
    } catch {
      setError('Ошибка при подборе. Попробуйте ещё раз.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-1">Подбор комплекта</h1>
      <p className="text-gray-400 text-sm mb-6">
        Система распределит бюджет между всеми категориями и подберёт оптимальный набор периферии.
      </p>

      <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-2xl p-6 mb-6">
        {/* Бюджет */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Общий бюджет (₽)
          </label>
          <input
            type="number"
            value={budget}
            onChange={(e) => setBudget(e.target.value)}
            placeholder="Например: 50000"
            min={5000}
            className="w-full border border-gray-200 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
            required
          />
        </div>

        {/* Сценарий */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Основное использование
          </label>
          <div className="grid grid-cols-3 gap-2">
            {USE_CASE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setUseCase(opt.value as SetupRequest['use_case'])}
                className={`border rounded-xl px-3 py-3 text-sm text-left transition-all ${
                  useCase === opt.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-blue-300'
                }`}
              >
                <div className="font-medium">{opt.label}</div>
                <div className="text-xs text-gray-400 mt-0.5">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Приоритет */}
        <div className="mb-5">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Что важнее
          </label>
          <div className="grid grid-cols-3 gap-2">
            {PRIORITY_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => setPriority(opt.value as SetupRequest['priority'])}
                className={`border rounded-xl px-3 py-3 text-sm text-left transition-all ${
                  priority === opt.value
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-gray-200 text-gray-600 hover:border-blue-300'
                }`}
              >
                <div className="font-medium">{opt.label}</div>
                <div className="text-xs text-gray-400 mt-0.5">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-red-500 text-sm mb-3">{error}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl py-3 transition-colors disabled:opacity-50"
        >
          {loading ? 'Подбираем комплект...' : 'Подобрать комплект'}
        </button>
      </form>

      {result && (
        <div>
          {/* Итог бюджета */}
          <div className="bg-white border border-gray-200 rounded-2xl p-4 mb-4 flex items-center justify-between">
            <div>
              <div className="text-sm text-gray-400">Итого</div>
              <div className="text-2xl font-bold text-gray-900">{formatPrice(result.total_price)}</div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-400">Бюджет</div>
              <div className="text-lg font-semibold text-gray-700">{formatPrice(result.total_budget)}</div>
            </div>
            <div className={`text-right ${result.remaining >= 0 ? 'text-green-600' : 'text-red-500'}`}>
              <div className="text-sm text-gray-400">Остаток</div>
              <div className="text-lg font-semibold">{formatPrice(Math.abs(result.remaining))}</div>
            </div>
          </div>

          {/* Карточки товаров */}
          <div className="flex flex-col gap-3">
            {Object.entries(result.items).map(([cat, item]) => (
              <div
                key={cat}
                onClick={() => setSelected(item)}
                className="bg-white border border-gray-200 rounded-2xl p-4 flex items-center gap-4 cursor-pointer hover:border-blue-300 hover:shadow-sm transition-all"
              >
                {/* Изображение */}
                <div className="w-16 h-16 bg-gray-50 rounded-lg flex items-center justify-center shrink-0 overflow-hidden">
                  {item.image_url
                    ? <img src={item.image_url} alt={item.name} className="max-w-full max-h-full object-contain" />
                    : <span className="text-gray-300 text-xs">Нет фото</span>
                  }
                </div>

                {/* Инфо */}
                <div className="flex-1 min-w-0">
                  <div className="text-xs text-gray-400 uppercase tracking-wide mb-0.5">
                    {CATEGORY_LABELS[cat] ?? cat}
                  </div>
                  <div className="text-sm font-medium text-gray-900 line-clamp-2 leading-snug">
                    {item.name}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Выделено: {formatPrice(result.allocations[cat])}
                  </div>
                </div>

                {/* Цена */}
                <div className="text-right shrink-0">
                  <div className="text-blue-600 font-bold">{formatPrice(item.best_price)}</div>
                  <div className="flex flex-col gap-1 mt-1">
                    {item.ozon_url && (
                      <a href={item.ozon_url} target="_blank" rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-gray-400 hover:text-blue-600 transition-colors">
                        Ozon →
                      </a>
                    )}
                    {item.citilink_url && (
                      <a href={item.citilink_url} target="_blank" rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-gray-400 hover:text-blue-600 transition-colors">
                        Ситилинк →
                      </a>
                    )}
                    {item.wb_url && (
                      <a href={item.wb_url} target="_blank" rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-gray-400 hover:text-blue-600 transition-colors">
                        WB →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {selected && (
        <ProductModal item={selected} onClose={() => setSelected(null)} />
      )}
    </main>
  )
}
