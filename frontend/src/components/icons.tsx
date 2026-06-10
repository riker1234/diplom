// Цветные SVG-иконки в стиле эмодзи.
// Заменяют эмодзи (🖱️⌨️🖥️🎧🎤🟦☀️🌙), которые на iOS рендерятся пустыми квадратами.

interface IconProps {
  className?: string
}

export function MouseIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <rect x="17" y="6" width="30" height="52" rx="15" fill="#e5e7eb" stroke="#9ca3af" strokeWidth="2.5" />
      <line x1="32" y1="8" x2="32" y2="26" stroke="#9ca3af" strokeWidth="2" />
      <rect x="28.5" y="13" width="7" height="11" rx="3.5" fill="#6b7280" />
    </svg>
  )
}

export function KeyboardIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <rect x="4" y="17" width="56" height="30" rx="4" fill="#374151" stroke="#1f2937" strokeWidth="2" />
      {[9, 17, 25, 33, 41, 49].map((x) => (
        <rect key={`r1-${x}`} x={x} y="22" width="6" height="5" rx="1" fill="#9ca3af" />
      ))}
      {[9, 17, 25, 33, 41, 49].map((x) => (
        <rect key={`r2-${x}`} x={x} y="29.5" width="6" height="5" rx="1" fill="#9ca3af" />
      ))}
      <rect x="9" y="37" width="6" height="5" rx="1" fill="#9ca3af" />
      <rect x="17.5" y="37" width="29" height="5" rx="1" fill="#9ca3af" />
      <rect x="49" y="37" width="6" height="5" rx="1" fill="#9ca3af" />
    </svg>
  )
}

export function MonitorIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <rect x="6" y="8" width="52" height="34" rx="3" fill="#1f2937" />
      <rect x="10" y="12" width="44" height="26" rx="1.5" fill="#60a5fa" />
      <rect x="26" y="42" width="12" height="7" fill="#9ca3af" />
      <rect x="17" y="49" width="30" height="5" rx="2.5" fill="#6b7280" />
    </svg>
  )
}

export function HeadphonesIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <path d="M12 38 v-6 a20 20 0 0 1 40 0 v6" fill="none" stroke="#1f2937" strokeWidth="5" strokeLinecap="round" />
      <rect x="8" y="34" width="13" height="19" rx="6" fill="#374151" />
      <rect x="43" y="34" width="13" height="19" rx="6" fill="#374151" />
    </svg>
  )
}

export function MicrophoneIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <g transform="rotate(-18 32 32)">
        <circle cx="32" cy="17" r="12" fill="#e5e7eb" stroke="#9ca3af" strokeWidth="2" />
        <line x1="22" y1="13" x2="42" y2="13" stroke="#9ca3af" strokeWidth="1.5" />
        <line x1="20" y1="18" x2="44" y2="18" stroke="#9ca3af" strokeWidth="1.5" />
        <line x1="22" y1="23" x2="42" y2="23" stroke="#9ca3af" strokeWidth="1.5" />
        <path d="M28 28 L36 28 L34.5 56 L29.5 56 Z" fill="#4b5563" />
      </g>
    </svg>
  )
}

export function MousepadIcon({ className = 'w-10 h-10' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <rect x="7" y="7" width="50" height="50" rx="10" fill="#3b82f6" />
      <rect x="12" y="12" width="40" height="40" rx="7" fill="none" stroke="#60a5fa" strokeWidth="2" />
    </svg>
  )
}

export function SunIcon({ className = 'w-5 h-5' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <circle cx="32" cy="32" r="11" fill="#fbbf24" />
      <g stroke="#fbbf24" strokeWidth="4.5" strokeLinecap="round">
        <line x1="32" y1="6" x2="32" y2="14" />
        <line x1="32" y1="50" x2="32" y2="58" />
        <line x1="6" y1="32" x2="14" y2="32" />
        <line x1="50" y1="32" x2="58" y2="32" />
        <line x1="13.6" y1="13.6" x2="19.3" y2="19.3" />
        <line x1="44.7" y1="44.7" x2="50.4" y2="50.4" />
        <line x1="13.6" y1="50.4" x2="19.3" y2="44.7" />
        <line x1="44.7" y1="19.3" x2="50.4" y2="13.6" />
      </g>
    </svg>
  )
}

export function MoonIcon({ className = 'w-5 h-5' }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" className={className} aria-hidden="true">
      <path d="M41 7 A 26 26 0 1 0 57 43 A 21 21 0 1 1 41 7 Z" fill="#fbbf24" />
    </svg>
  )
}
