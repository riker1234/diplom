import { useState, useRef } from 'react'
import { useEffect } from 'react'

interface TooltipProps {
  short: string
  detail?: string
}

export default function Tooltip({ short, detail }: TooltipProps) {
  const [visible, setVisible] = useState(false)
  // На мобильном открываем вниз и выбираем сторону по позиции кнопки,
  // чтобы подсказка не уезжала за край экрана. На десктопе — как раньше (вправо).
  const [mobile, setMobile] = useState(false)
  const [alignRight, setAlignRight] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!visible) return
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setVisible(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [visible])

  function toggle(e: React.MouseEvent) {
    e.stopPropagation()
    if (!visible && ref.current) {
      const rect = ref.current.getBoundingClientRect()
      setMobile(window.matchMedia('(max-width: 639px)').matches)
      setAlignRight(rect.left > window.innerWidth / 2)
    }
    setVisible(v => !v)
  }

  const popupPosition = mobile
    ? `top-6 ${alignRight ? 'right-0' : 'left-0'} max-w-[calc(100vw-2rem)]`
    : 'left-5 top-0'

  return (
    <div ref={ref} className="relative inline-flex items-center ml-1">
      <button
        type="button"
        onClick={toggle}
        className="w-4 h-4 rounded-full bg-gray-200 dark:bg-gray-600 hover:bg-blue-100 dark:hover:bg-blue-900 text-gray-500 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 text-xs flex items-center justify-center transition-colors shrink-0"
        aria-label="Подробнее"
      >
        ?
      </button>
      {visible && (
        <div className={`absolute z-50 w-64 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg p-3 text-sm ${popupPosition}`}>
          <p className="font-medium text-gray-800 dark:text-white mb-1">{short}</p>
          {detail && <p className="text-gray-500 dark:text-gray-400 text-xs leading-relaxed">{detail}</p>}
        </div>
      )}
    </div>
  )
}
