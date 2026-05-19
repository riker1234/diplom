import { useEffect } from 'react'

const FIELD_LABELS: Record<string, string> = {
  brand: 'Бренд',
  keyboard_type: 'Тип клавиатуры',
  switches: 'Переключатели',
  form_factor: 'Форм-фактор',
  connection_types: 'Подключение',
  board_material: 'Материал корпуса',
  keycap_material: 'Материал клавиш',
  keycap_manufacturing: 'Производство клавиш',
  sensor: 'Сенсор',
  weight_g: 'Вес, г',
  max_dpi: 'Макс. DPI',
  buttons_count: 'Кол-во кнопок',
  diagonal_inch: 'Диагональ, дюйм',
  refresh_rate_hz: 'Частота обновления, Гц',
  matrix_type: 'Тип матрицы',
  resolution: 'Разрешение',
  has_microphone: 'Микрофон',
  mic_type: 'Тип микрофона',
  frequency_response: 'Частотный диапазон',
  hardness: 'Жёсткость',
  has_rgb: 'RGB-подсветка',
  size_mm: 'Размер, мм',
  material: 'Материал',
}

const SKIP_FIELDS = new Set([
  'id', 'name', 'image_url', 'ozon_url', 'wb_url', 'dns_url', 'citilink_url',
  'source', 'updated_at', 'price', 'wb_price', 'citilink_price', 'dns_price',
  'ozon_sku', 'wb_sku', 'dns_sku', 'citilink_sku', 'dns_product_id',
])

function formatValue(key: string, val: unknown): string {
  if (typeof val === 'boolean') return val ? 'Да' : 'Нет'
  if (val === null || val === undefined || val === '') return ''
  return String(val)
}

function formatPrice(p: number | null | undefined) {
  if (p == null) return null
  return p.toLocaleString('ru-RU') + ' ₽'
}

interface Props {
  item: Record<string, unknown>
  onClose: () => void
}

export default function ProductModal({ item, onClose }: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const specs = Object.entries(item)
    .filter(([key, val]) => {
      if (SKIP_FIELDS.has(key)) return false
      if (val === null || val === undefined || val === '') return false
      return FIELD_LABELS[key] !== undefined
    })
    .map(([key, val]) => ({ label: FIELD_LABELS[key], value: formatValue(key, val) }))
    .filter((s) => s.value !== '')

  const storeLinks = [
    item.ozon_url && { label: 'Ozon', url: item.ozon_url as string, price: item.price as number | null },
    item.wb_url && { label: 'Wildberries', url: item.wb_url as string, price: item.wb_price as number | null },
    item.dns_url && { label: 'DNS', url: item.dns_url as string, price: null },
    item.citilink_url && { label: 'Ситилинк', url: item.citilink_url as string, price: item.citilink_price as number | null },
  ].filter(Boolean) as { label: string; url: string; price: number | null }[]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 px-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between p-5 border-b border-gray-100">
          <div className="pr-4">
            {item.brand && (
              <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
                {String(item.brand)}
              </div>
            )}
            <h2 className="font-semibold text-gray-900 text-base leading-snug">
              {String(item.name)}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none shrink-0"
          >
            ✕
          </button>
        </div>

        {/* Image */}
        {item.image_url && (
          <div className="flex items-center justify-center bg-gray-50 p-6 h-52">
            <img
              src={String(item.image_url)}
              alt={String(item.name)}
              className="max-h-full max-w-full object-contain"
            />
          </div>
        )}

        {/* Specs */}
        {specs.length > 0 && (
          <div className="p-5">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Характеристики
            </h3>
            <div className="divide-y divide-gray-100">
              {specs.map((s) => (
                <div key={s.label} className="flex justify-between py-2 gap-4">
                  <span className="text-sm text-gray-500">{s.label}</span>
                  <span className="text-sm text-gray-900 text-right">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Store links */}
        {storeLinks.length > 0 && (
          <div className="p-5 pt-0">
            <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Купить
            </h3>
            <div className="flex flex-col gap-2">
              {storeLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center justify-between bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl px-4 py-3 transition-colors"
                >
                  <span className="font-medium text-gray-700">{link.label}</span>
                  {link.price != null && (
                    <span className="font-bold text-blue-600">{formatPrice(link.price)}</span>
                  )}
                </a>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
