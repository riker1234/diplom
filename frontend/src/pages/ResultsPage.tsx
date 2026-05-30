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

function formatUpdatedAt(updatedAt: string | null): string | null {
  if (!updatedAt) return null
  const d = new Date(updatedAt)
  const now = new Date()
  const diffDays = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))
  if (diffDays === 0) return 'сегодня'
  if (diffDays === 1) return 'вчера'
  if (diffDays < 7) return `${diffDays} дн. назад`
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
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

function RankBadge({ rank, score }: { rank: number; score: number }) {
  const base = "absolute top-2 left-2 flex items-center gap-1"

  if (rank === 1) return (
    <div className={base}>
      <div className="w-8 h-8 rounded-full bg-yellow-400 border-2 border-yellow-300 shadow-md flex items-center justify-center shrink-0">
        <span className="text-white text-xs font-black">1</span>
      </div>
      <span className="bg-yellow-400 text-white text-xs font-semibold px-1.5 py-0.5 rounded-full shadow-sm">
        {score} б.
      </span>
    </div>
  )
  if (rank === 2) return (
    <div className={base}>
      <div className="w-8 h-8 rounded-full bg-gray-400 border-2 border-gray-300 shadow-md flex items-center justify-center shrink-0">
        <span className="text-white text-xs font-black">2</span>
      </div>
      <span className="bg-gray-400 text-white text-xs font-semibold px-1.5 py-0.5 rounded-full shadow-sm">
        {score} б.
      </span>
    </div>
  )
  if (rank === 3) return (
    <div className={base}>
      <div className="w-8 h-8 rounded-full bg-amber-600 border-2 border-amber-500 shadow-md flex items-center justify-center shrink-0">
        <span className="text-white text-xs font-black">3</span>
      </div>
      <span className="bg-amber-600 text-white text-xs font-semibold px-1.5 py-0.5 rounded-full shadow-sm">
        {score} б.
      </span>
    </div>
  )
  return (
    <div className={base}>
      <div className="w-7 h-7 rounded-full bg-white border border-gray-200 shadow-sm flex items-center justify-center shrink-0">
        <span className="text-gray-500 text-xs font-semibold">{rank}</span>
      </div>
      <span className="bg-white text-gray-500 text-xs font-medium px-1.5 py-0.5 rounded-full shadow-sm border border-gray-200">
        {score} б.
      </span>
    </div>
  )
}

function ProductCard({
  item,
  rank,
  onClick,
}: {
  item: RecommendResultItem
  rank: number
  onClick: () => void
}) {
  return (
    <div
      onClick={onClick}
      className={`bg-white border rounded-xl overflow-hidden hover:shadow-md transition-all flex flex-col cursor-pointer ${
        rank === 1
          ? 'border-yellow-300 shadow-sm'
          : rank <= 3
          ? 'border-gray-300'
          : 'border-gray-200 hover:border-blue-300'
      }`}
    >
      <div className="relative">
        <ImageBox url={item.image_url} name={item.name} />
        <RankBadge rank={rank} score={item.score} />
      </div>
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
        {item.updated_at && (
          <div className="text-xs text-gray-400 mt-1.5">
            Данные: {formatUpdatedAt(item.updated_at)}
          </div>
        )}
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

      {results.length > 0 && (
        <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 mb-4 -mt-1">
          <svg className="w-4 h-4 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M12 2a10 10 0 100 20A10 10 0 0012 2z" />
          </svg>
          <p className="text-xs text-amber-700 font-medium">
            Цены актуальны на момент последнего обновления данных — уточняйте наличие на сайте магазина.
          </p>
        </div>
      )}

      {results.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="mb-4">По вашим параметрам ничего не найдено.</p>
          <button onClick={() => navigate(-1)} className="text-blue-600 hover:underline">
            Попробовать снова
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {results.map((item, index) => (
            <ProductCard key={item.id} item={item} rank={index + 1} onClick={() => setSelected(item)} />
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
