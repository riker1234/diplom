import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { fetchQuestions, fetchRecommendations } from '../api'
import type { Question } from '../api'

const CATEGORY_LABELS: Record<string, string> = {
  mouse: 'Мышь',
  keyboard: 'Клавиатура',
  monitor: 'Монитор',
  headphones: 'Наушники',
  microphone: 'Микрофон',
  mousepad: 'Коврик',
}

export default function QuizPage() {
  const { category } = useParams<{ category: string }>()
  const navigate = useNavigate()

  const [questions, setQuestions] = useState<Question[]>([])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState<Record<string, string | number>>({})
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!category) return
    fetchQuestions(category)
      .then(setQuestions)
      .catch(() => setError('Не удалось загрузить вопросы'))
      .finally(() => setLoading(false))
  }, [category])

  const current = questions[step]

  function handleChoice(value: string) {
    const updated = { ...answers, [current.id]: value }
    setAnswers(updated)
    if (step + 1 < questions.length) {
      setStep(step + 1)
    } else {
      submit(updated)
    }
  }

  function handleNumber(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const val = (e.currentTarget.elements.namedItem('num') as HTMLInputElement).value
    const updated = { ...answers, [current.id]: Number(val) }
    setAnswers(updated)
    if (step + 1 < questions.length) {
      setStep(step + 1)
    } else {
      submit(updated)
    }
  }

  async function submit(finalAnswers: Record<string, string | number>) {
    if (!category) return
    setSubmitting(true)
    try {
      const results = await fetchRecommendations(category, finalAnswers)
      navigate('/results', { state: { results, category } })
    } catch {
      setError('Ошибка при подборе. Попробуйте ещё раз.')
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center text-gray-400">
        Загрузка вопросов...
      </div>
    )
  }

  if (error) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center">
        <p className="text-red-500 mb-4">{error}</p>
        <button onClick={() => navigate('/')} className="text-blue-600 hover:underline">
          На главную
        </button>
      </div>
    )
  }

  if (submitting) {
    return (
      <div className="max-w-lg mx-auto px-4 py-16 text-center text-gray-400">
        Подбираем варианты...
      </div>
    )
  }

  if (!current) return null

  const progress = (step / questions.length) * 100

  return (
    <main className="max-w-lg mx-auto px-4 py-10">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2 text-sm text-gray-400">
          <span>{CATEGORY_LABELS[category!] ?? category}</span>
          <span>
            {step + 1} / {questions.length}
          </span>
        </div>
        <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <h2 className="text-xl font-semibold text-gray-900 mb-6">{current.text}</h2>

      {current.type === 'choice' && current.options && (
        <div className="flex flex-col gap-3">
          {current.options.map((opt) => (
            <button
              key={opt.value}
              onClick={() => handleChoice(opt.value)}
              className="border border-gray-200 rounded-xl px-5 py-4 text-left hover:border-blue-400 hover:bg-blue-50 transition-all text-gray-800 cursor-pointer"
            >
              {opt.label}
            </button>
          ))}
        </div>
      )}

      {current.type === 'number' && (
        <form onSubmit={handleNumber} className="flex flex-col gap-4">
          <input
            name="num"
            type="number"
            min={0}
            placeholder={current.placeholder ?? ''}
            className="border border-gray-300 rounded-xl px-4 py-3 text-gray-900 focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
            required
          />
          <button
            type="submit"
            className="bg-blue-600 text-white rounded-xl px-6 py-3 font-medium hover:bg-blue-700 transition-colors"
          >
            Далее
          </button>
        </form>
      )}

      {step > 0 && (
        <button
          onClick={() => setStep(step - 1)}
          className="mt-6 text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          ← Назад
        </button>
      )}
    </main>
  )
}
