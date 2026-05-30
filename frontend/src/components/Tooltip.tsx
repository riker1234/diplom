import { useState, useRef, useEffect } from 'react'

interface TooltipProps {
  short: string
  detail?: string
}

export default function Tooltip({ short, detail }: TooltipProps) {
  const [visible, setVisible] = useState(false)
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

  return (
    <div ref={ref} className="relative inline-flex items-center ml-1">
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setVisible(v => !v) }}
        className="w-4 h-4 rounded-full bg-gray-200 hover:bg-blue-100 text-gray-500 hover:text-blue-600 text-xs flex items-center justify-center transition-colors shrink-0"
        aria-label="Подробнее"
      >
        ?
      </button>
      {visible && (
        <div className="absolute z-50 left-5 top-0 w-64 bg-white border border-gray-200 rounded-xl shadow-lg p-3 text-sm">
          <p className="font-medium text-gray-800 mb-1">{short}</p>
          {detail && <p className="text-gray-500 text-xs leading-relaxed">{detail}</p>}
        </div>
      )}
    </div>
  )
}
