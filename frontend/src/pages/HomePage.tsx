import { useNavigate } from 'react-router-dom'

const CATEGORIES = [
  { id: 'mouse', label: 'Мышь', icon: '🖱️', desc: 'Игровые и офисные мыши' },
  { id: 'keyboard', label: 'Клавиатура', icon: '⌨️', desc: 'Механические и мембранные' },
  { id: 'monitor', label: 'Монитор', icon: '🖥️', desc: 'Игровые и рабочие мониторы' },
  { id: 'headphones', label: 'Наушники', icon: '🎧', desc: 'Гарнитуры и наушники' },
  { id: 'microphone', label: 'Микрофон', icon: '🎤', desc: 'USB и XLR микрофоны' },
  { id: 'mousepad', label: 'Коврик', icon: '🟦', desc: 'Мягкие и жёсткие коврики' },
]

export default function HomePage() {
  const navigate = useNavigate()

  return (
    <main className="max-w-5xl mx-auto px-4 py-12">
      <div className="text-center mb-10">
        <h1 className="text-3xl font-bold text-gray-900 mb-3">
          Подбор периферии для ПК
        </h1>
        <p className="text-gray-500 text-lg">
          Ответьте на несколько вопросов — подберём лучшие варианты по вашему бюджету
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.id}
            onClick={() => navigate(`/quiz/${cat.id}`)}
            className="bg-white border border-gray-200 rounded-xl p-6 text-left hover:border-blue-400 hover:shadow-md transition-all group cursor-pointer"
          >
            <div className="text-4xl mb-3">{cat.icon}</div>
            <div className="font-semibold text-gray-900 group-hover:text-blue-600 text-lg transition-colors">
              {cat.label}
            </div>
            <div className="text-sm text-gray-400 mt-1">{cat.desc}</div>
          </button>
        ))}
      </div>
    </main>
  )
}
