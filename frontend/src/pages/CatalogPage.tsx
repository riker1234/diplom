import { useEffect, useState } from 'react'
import { fetchCatalog } from '../api'
import ProductModal from '../components/ProductModal'

const CATEGORIES = [
  { id: 'mouse', label: 'Мыши' },
  { id: 'keyboard', label: 'Клавиатуры' },
  { id: 'monitor', label: 'Мониторы' },
  { id: 'headphones', label: 'Наушники' },
  { id: 'microphone', label: 'Микрофоны' },
  { id: 'mousepad', label: 'Коврики' },
]

const SOURCES = [
  { id: 'ozon', label: 'Ozon' },
  { id: 'wb', label: 'Wildberries' },
  { id: 'citilink', label: 'Ситилинк' },
]

const SORT_OPTIONS = [
  { id: 'default', label: 'По умолчанию' },
  { id: 'price_asc', label: 'Сначала дешевле' },
  { id: 'price_desc', label: 'Сначала дороже' },
  { id: 'name_asc', label: 'По названию А-Я' },
]

function matchesSources(item: any, sources: Set<string>): boolean {
  if (sources.size === 0) return true
  if (sources.has('ozon') && !item.ozon_url) return false
  if (sources.has('wb') && !item.wb_url) return false
  if (sources.has('citilink') && !item.citilink_url) return false
  return true
}

function formatPrice(p: number | null | undefined) {
  if (p == null) return null
  return p.toLocaleString('ru-RU') + ' ₽'
}

function displayBrand(brand: string | null | undefined): string {
  const s = (brand ?? '').trim()
  if (!s || /^\d+(\.\d+)?$/.test(s) || s.toLowerCase() === 'оригинал') return 'Неизвестно'
  return s
}

function bestPrice(item: any): number | null {
  const prices = [item.price, item.wb_price, item.citilink_price].filter(
    (p): p is number => p != null
  )
  return prices.length ? Math.min(...prices) : null
}

function ImageBox({ url, name }: { url: string | null; name: string }) {
  const [failed, setFailed] = useState(false)

  if (!url || failed) {
    return (
      <div className="h-36 bg-gray-100 flex items-center justify-center shrink-0">
        <span className="text-gray-300 text-sm">Нет фото</span>
      </div>
    )
  }

  return (
    <div className="h-36 bg-gray-50 flex items-center justify-center p-3 shrink-0">
      <img
        src={url}
        alt={name}
        className="max-h-full max-w-full object-contain"
        onError={() => setFailed(true)}
      />
    </div>
  )
}

export default function CatalogPage() {
  const [category, setCategory] = useState('mouse')
  const [sources, setSources] = useState<Set<string>>(new Set())
  const [sort, setSort] = useState('default')
  const [priceMin, setPriceMin] = useState('')
  const [priceMax, setPriceMax] = useState('')
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [selected, setSelected] = useState<any | null>(null)

  useEffect(() => {
    const params: Record<string, string> = {}
    if (priceMin) params.price_min = priceMin
    if (priceMax) params.price_max = priceMax

    setLoading(true)
    fetchCatalog(category, params)
      .then(setItems)
      .catch(() => setItems([]))
      .finally(() => setLoading(false))
  }, [category, priceMin, priceMax])

  const filtered = items
    .filter((item) => matchesSources(item, sources))
    .sort((a, b) => {
      if (sort === 'price_asc') return (bestPrice(a) ?? Infinity) - (bestPrice(b) ?? Infinity)
      if (sort === 'price_desc') return (bestPrice(b) ?? 0) - (bestPrice(a) ?? 0)
      if (sort === 'name_asc') return (a.name ?? '').localeCompare(b.name ?? '', 'ru')
      return 0
    })

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Каталог</h1>

      {/* Category tabs */}
      <div className="flex gap-2 flex-wrap mb-4">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setCategory(cat.id)}
            className={`px-4 py-1.5 rounded-full text-sm font-medium border transition-colors cursor-pointer ${
              category === cat.id
                ? 'bg-blue-600 text-white border-blue-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300'
            }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Source filter */}
      <div className="flex gap-2 flex-wrap mb-5 items-center">
        <button
          onClick={() => setSources(new Set())}
          className={`px-3 py-1 rounded-full text-sm border transition-colors cursor-pointer ${
            sources.size === 0
              ? 'bg-gray-800 text-white border-gray-800'
              : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
          }`}
        >
          Все
        </button>
        {SOURCES.map((s) => (
          <button
            key={s.id}
            onClick={() => {
              setSources(prev => {
                const next = new Set(prev)
                next.has(s.id) ? next.delete(s.id) : next.add(s.id)
                return next
              })
            }}
            className={`px-3 py-1 rounded-full text-sm border transition-colors cursor-pointer ${
              sources.has(s.id)
                ? 'bg-gray-800 text-white border-gray-800'
                : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Sort + Price filter */}
      <div className="flex gap-3 items-center flex-wrap mb-6">
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 focus:outline-none focus:border-blue-400 cursor-pointer"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.id} value={o.id}>{o.label}</option>
          ))}
        </select>
        <span className="text-gray-300">|</span>
      </div>
      <div className="flex gap-3 items-center flex-wrap mb-6">
        <span className="text-sm text-gray-500">Цена:</span>
        <input
          type="number"
          value={priceMin}
          onChange={(e) => setPriceMin(e.target.value)}
          placeholder="от"
          className="w-24 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-blue-400"
        />
        <span className="text-gray-400">—</span>
        <input
          type="number"
          value={priceMax}
          onChange={(e) => setPriceMax(e.target.value)}
          placeholder="до"
          className="w-24 border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:border-blue-400"
        />
        <span className="text-sm text-gray-500">₽</span>
        {(priceMin || priceMax) && (
          <button
            onClick={() => { setPriceMin(''); setPriceMax('') }}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Сбросить
          </button>
        )}
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-400">Загрузка...</div>
      ) : (
        <>
          <p className="text-sm text-gray-400 mb-4">{filtered.length} товаров</p>

          {filtered.length === 0 ? (
            <div className="text-center py-16 text-gray-400">Товары не найдены</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {filtered.map((item) => {
                const bp = bestPrice(item)
                const links = [
                  item.ozon_url && { label: 'Ozon', url: item.ozon_url, price: item.price },
                  item.wb_url && { label: 'WB', url: item.wb_url, price: item.wb_price },
                  item.dns_url && { label: 'DNS', url: item.dns_url, price: null },
                  item.citilink_url && { label: 'Ситилинк', url: item.citilink_url, price: item.citilink_price },
                ].filter(Boolean) as { label: string; url: string; price: number | null }[]

                return (
                  <div
                    key={item.id}
                    onClick={() => setSelected(item)}
                    className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-md hover:border-blue-300 transition-all flex flex-col cursor-pointer"
                  >
                    <ImageBox url={item.image_url} name={item.name} />
                    <div className="p-3 flex flex-col flex-1">
                      <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                        {displayBrand(item.brand)}
                      </div>
                      <h3 className="font-medium text-gray-900 text-sm leading-snug mb-2 line-clamp-2 flex-1">
                        {item.name}
                      </h3>
                      {bp != null && (
                        <div className="text-blue-600 font-bold text-base mb-2">
                          от {formatPrice(bp)}
                        </div>
                      )}
                      <div className="flex gap-1 flex-wrap">
                        {links.map((link) => (
                          <a
                            key={link.label}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="text-xs bg-gray-100 hover:bg-gray-200 rounded px-2 py-1 text-gray-600 transition-colors"
                          >
                            {link.label}
                            {link.price != null ? ` ${formatPrice(link.price)}` : ''}
                          </a>
                        ))}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </>
      )}

      {selected && (
        <ProductModal item={selected} onClose={() => setSelected(null)} />
      )}
    </main>
  )
}
