import { useState } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import type { RecommendResultItem } from '../api'
import ProductModal from '../components/ProductModal'

const CATEGORY_LABELS: Record<string, string> = {
  mouse: 'Мышь',
  keyboard: 'Клавиатура',
  monitor: 'Монитор',
  headphones: 'Наушники',
  microphone: 'Микрофон',
  mousepad: 'Коврик',
}

function formatPrice(p: number | null | undefined) {
  if (p == null) return null
  return p.toLocaleString('ru-RU') + ' ₽'
}

function ImageBox({ url, name }: { url: string | null; name: string }) {
  const [failed, setFailed] = useState(false)

  if (!url || failed) {
    return (
      <div className="h-44 bg-gray-100 flex items-center justify-center shrink-0">
        <span className="text-gray-300 text-sm">Нет фото</span>
      </div>
    )
  }

  return (
    <div className="h-44 bg-gray-50 flex items-center justify-center p-4 shrink-0">
      <img
        src={url}
        alt={name}
        className="max-h-full max-w-full object-contain"
        onError={() => setFailed(true)}
      />
    </div>
  )
}

function ProductCard({
  item,
  onClick,
}: {
  item: RecommendResultItem
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md hover:border-blue-300 transition-all flex flex-col cursor-pointer"
    >
      <ImageBox url={item.image_url} name={item.name} />
      <div className="p-4 flex flex-col flex-1">
        {item.brand && (
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">{item.brand}</div>
        )}
        <h3 className="font-medium text-gray-900 text-sm leading-snug mb-3 line-clamp-2 flex-1">
          {item.name}
        </h3>
        {item.best_price != null && (
          <div className="text-blue-600 font-bold text-lg mb-3">
            от {formatPrice(item.best_price)}
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          {item.ozon_url && (
            <a
              href={item.ozon_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm transition-colors"
            >
              <span className="text-gray-600 font-medium">Ozon</span>
              {item.price != null && <span className="font-semibold text-gray-900">{formatPrice(item.price)}</span>}
            </a>
          )}
          {item.wb_url && (
            <a
              href={item.wb_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm transition-colors"
            >
              <span className="text-gray-600 font-medium">Wildberries</span>
              {item.wb_price != null && <span className="font-semibold text-gray-900">{formatPrice(item.wb_price)}</span>}
            </a>
          )}
          {item.dns_url && (
            <a
              href={item.dns_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm transition-colors"
            >
              <span className="text-gray-600 font-medium">DNS</span>
            </a>
          )}
          {item.citilink_url && (
            <a
              href={item.citilink_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg px-3 py-2 text-sm transition-colors"
            >
              <span className="text-gray-600 font-medium">Ситилинк</span>
              {item.citilink_price != null && <span className="font-semibold text-gray-900">{formatPrice(item.citilink_price)}</span>}
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ResultsPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const [selected, setSelected] = useState<RecommendResultItem | null>(null)

  const state = (location.state ?? {}) as {
    results?: RecommendResultItem[]
    category?: string
  }
  const { results, category } = state

  if (!results || !category) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <p className="text-gray-400 mb-4">Нет результатов. Пройдите подбор заново.</p>
        <Link to="/" className="text-blue-600 hover:underline">На главную</Link>
      </div>
    )
  }

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6 flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Результаты подбора</h1>
          <p className="text-gray-400 text-sm mt-1">
            {CATEGORY_LABELS[category] ?? category} · {results.length} вариантов
          </p>
        </div>
        <button
          onClick={() => navigate(`/quiz/${category}`)}
          className="text-sm text-blue-600 hover:underline"
        >
          Изменить ответы
        </button>
      </div>

      {results.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="mb-4">По вашим параметрам ничего не найдено.</p>
          <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline">
            Попробовать снова
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {results.map((item) => (
            <ProductCard key={item.id} item={item} onClick={() => setSelected(item)} />
          ))}
        </div>
      )}

      {selected && (
        <ProductModal
          item={selected as unknown as Record<string, unknown>}
          onClose={() => setSelected(null)}
        />
      )}
    </main>
  )
}
