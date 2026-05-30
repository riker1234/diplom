import { useEffect, useState } from 'react'
import Tooltip from './Tooltip'
import { CHAR_DESCRIPTIONS } from '../charDescriptions'

const FIELD_LABELS: Record<string, string> = {
  // Общие
  brand: 'Бренд',
  color: 'Цвет',
  has_rgb: 'RGB-подсветка',
  connection_types: 'Подключение',
  interface: 'Интерфейс',
  // Мышь
  sensor: 'Сенсор',
  max_dpi: 'Макс. DPI',
  weight_g: 'Вес, г',
  button_count: 'Кол-во кнопок',
  // Клавиатура
  keyboard_type: 'Тип клавиатуры',
  switches: 'Переключатели',
  form_factor: 'Форм-фактор',
  key_count: 'Кол-во клавиш',
  layout: 'Раскладка',
  keycap_material: 'Материал клавиш',
  keycap_manufacturing: 'Нанесение символов',
  board_material: 'Материал корпуса',
  // Монитор
  diagonal_inch: 'Диагональ, дюйм',
  resolution: 'Разрешение',
  refresh_rate_hz: 'Частота обновления, Гц',
  matrix_type: 'Тип матрицы',
  response_time_ms: 'Время отклика, мс',
  brightness_nits: 'Яркость, кд/м²',
  hdr: 'HDR',
  // Наушники
  construction_type: 'Конструкция',
  has_microphone: 'Микрофон',
  impedance_ohm: 'Импеданс, Ом',
  frequency_response: 'Частотный диапазон',
  noise_cancellation: 'Шумоподавление',
  // Микрофон
  mic_type: 'Тип микрофона',
  directionality: 'Направленность',
  frequency_range: 'Частотный диапазон',
  sample_rate: 'Частота дискретизации',
  bit_depth: 'Разрядность',
  // Коврик
  size: 'Размер',
  surface_material: 'Материал поверхности',
  hardness: 'Жёсткость',
  thickness_mm: 'Толщина, мм',
}

const SKIP_FIELDS = new Set([
  'id', 'name', 'image_url', 'ozon_url', 'wb_url', 'dns_url', 'citilink_url',
  'source', 'updated_at', 'price', 'wb_price', 'citilink_price', 'dns_price',
  'ozon_sku', 'wb_sku', 'dns_sku', 'citilink_sku', 'dns_product_id',
])

// Russian adjective endings (конденсаторный, игровой, беспроводной, динамический...)
const _ADJ_RE = /(ный|ной|вой|ской|ский|ная|ное)$/i

function displayBrand(brand: unknown): string {
  const s = String(brand ?? '').trim()
  if (!s || /^\d+(\.\d+)?$/.test(s)) return 'Неизвестно'
  const lower = s.toLowerCase()
  if (lower === 'оригинал' || _ADJ_RE.test(lower)) return 'Неизвестно'
  return s
}

function formatValue(key: string, val: unknown): string {
  if (key === 'brand') return displayBrand(val)
  if (typeof val === 'boolean') return val ? 'Да' : 'Нет'
  if (val === null || val === undefined || val === '') return ''
  return String(val)
}

function formatPrice(p: number | null | undefined) {
  if (p == null) return null
  return p.toLocaleString('ru-RU') + ' ₽'
}

function formatDate(dt: unknown): string | null {
  if (!dt) return null
  try {
    return new Date(String(dt)).toLocaleDateString('ru-RU', {
      day: 'numeric', month: 'long', year: 'numeric',
    })
  } catch {
    return null
  }
}

interface Props {
  item: Record<string, unknown>
  onClose: () => void
}

export default function ProductModal({ item, onClose }: Props) {
  const [showBreakdown, setShowBreakdown] = useState(false)

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
    .map(([key, val]) => ({ key, label: FIELD_LABELS[key], value: formatValue(key, val) }))
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
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">
              {displayBrand(item.brand)}
            </div>
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
                  <span className="text-sm text-gray-500 flex items-center">
                    {s.label}
                    {CHAR_DESCRIPTIONS[s.key] && (
                      <Tooltip
                        short={CHAR_DESCRIPTIONS[s.key].short}
                        detail={CHAR_DESCRIPTIONS[s.key].detail}
                      />
                    )}
                  </span>
                  <span className="text-sm text-gray-900 text-right">{s.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Score breakdown */}
        {Array.isArray(item.score_breakdown) && (item.score_breakdown as any[]).length > 0 && (
          <div className="px-5 pb-2">
            <button
              onClick={() => setShowBreakdown(v => !v)}
              className="w-full flex items-center justify-between text-sm text-blue-600 hover:text-blue-700 font-medium py-2 border-t border-gray-100"
            >
              <span>За что начислены баллы?</span>
              <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full font-semibold">
                {item.score as number} б.
              </span>
            </button>
            {showBreakdown && (
              <div className="mt-1 mb-3 flex flex-col gap-1.5">
                {(item.score_breakdown as any[]).map((b: any, i: number) => (
                  <div key={i} className={`flex items-center justify-between rounded-lg px-3 py-1.5 text-xs ${
                    b.positive
                      ? 'bg-green-50 text-green-700'
                      : 'bg-red-50 text-red-600'
                  }`}>
                    <span>{b.label}</span>
                    <span className="font-bold shrink-0 ml-2">
                      {b.positive ? '+' : ''}{b.points} б.
                    </span>
                  </div>
                ))}
              </div>
            )}
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

        {/* Footer: data freshness */}
        <div className="px-5 pb-5 pt-3 border-t border-gray-100">
          <div className="bg-amber-50 border border-amber-200 rounded-lg px-3 py-2.5 flex flex-col gap-1">
            <div className="flex items-center gap-1.5">
              <svg className="w-3.5 h-3.5 text-amber-600 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
              </svg>
              <span className="text-xs text-amber-700 font-semibold">
                {formatDate(item.updated_at) ? `Данные обновлены: ${formatDate(item.updated_at)}` : 'Дата обновления неизвестна'}
              </span>
            </div>
            <p className="text-xs text-amber-700 pl-5">
              Цены и наличие могут отличаться — проверяйте на сайте магазина
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
