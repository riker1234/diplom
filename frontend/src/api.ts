const BASE = 'http://localhost:8000'

export interface QuestionOption {
  value: string
  label: string
}

export interface Question {
  id: string
  text: string
  type: 'choice' | 'number'
  options?: QuestionOption[]
  placeholder?: string
}

export interface ScoreBreakdownItem {
  label: string
  points: number
  positive: boolean
}

export interface RecommendResultItem {
  id: number
  name: string
  brand: string | null
  price: number | null
  wb_price: number | null
  citilink_price: number | null
  best_price: number | null
  score: number
  score_breakdown: ScoreBreakdownItem[]
  image_url: string | null
  ozon_url: string | null
  dns_url: string | null
  wb_url: string | null
  citilink_url: string | null
  updated_at: string | null
}

export async function fetchQuestions(category: string): Promise<Question[]> {
  const res = await fetch(`${BASE}/recommend/questions/${category}`)
  if (!res.ok) throw new Error('Failed to fetch questions')
  const data = await res.json()
  return data.questions
}

export async function fetchRecommendations(
  category: string,
  answers: Record<string, string | number>
): Promise<RecommendResultItem[]> {
  const res = await fetch(`${BASE}/recommend/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ category, answers }),
  })
  if (!res.ok) throw new Error('Failed to fetch recommendations')
  const data = await res.json()
  return data.results
}

const ENDPOINTS: Record<string, string> = {
  mouse: 'mice',
  keyboard: 'keyboards',
  monitor: 'monitors',
  headphones: 'headphones',
  microphone: 'microphones',
  mousepad: 'mousepads',
}

export interface SetupRequest {
  total_budget: number
  use_case: 'gaming' | 'work' | 'both'
  priority: 'budget' | 'balance' | 'flagship'
}

export interface SetupResult {
  use_case: string
  total_budget: number
  total_price: number
  remaining: number
  allocations: Record<string, number>
  items: Record<string, RecommendResultItem>
}

export async function fetchSetupRecommendation(req: SetupRequest): Promise<SetupResult> {
  const res = await fetch(`${BASE}/recommend/setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error('Failed to fetch setup recommendation')
  return res.json()
}

export async function fetchCatalog(
  category: string,
  params: Record<string, string>
): Promise<any[]> {
  const endpoint = ENDPOINTS[category]
  if (!endpoint) return []
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`${BASE}/${endpoint}/${qs ? '?' + qs : ''}`)
  if (!res.ok) throw new Error('Failed to fetch catalog')
  return res.json()
}
