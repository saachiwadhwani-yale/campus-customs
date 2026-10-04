export interface SizeStock {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  inventory: SizeStock[]
  total_stock: number
}

// Compact product summary the chatbot returns (mirrors ProductCard in models.py)
export interface ProductCard {
  product_id: string
  name: string
  price: number
  garment_type: string
  image_url: string
  description: string
  colors: string[]
  available_sizes: string[]
  stock_by_size?: Record<string, number>
  in_stock: boolean
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  products: ProductCard[]
}

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: ProductCard[]
}

export interface User {
  id: number
  first_name: string
  last_name: string
  name: string
  email: string
  created_at: string
}

export interface SignupData {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

async function getJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init)
  if (!res.ok) {
    // FastAPI puts the error message in `detail`
    const body = await res.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : `${res.status} ${res.statusText}`
    throw new Error(detail)
  }
  return res.json() as Promise<T>
}

const postJson = <T>(url: string, data: unknown) =>
  getJson<T>(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

export const fetchProducts = () => getJson<Product[]>('/api/products')

export const fetchProduct = (id: string) =>
  getJson<Product>(`/api/products/${encodeURIComponent(id)}`)

export const sendChat = (
  message: string,
  history: ChatTurn[] = [],
  userId: number | null = null,
  pageProductIds: string[] = [],
) =>
  postJson<ChatResponse>('/api/chat', {
    message,
    history,
    user_id: userId,
    page_product_ids: pageProductIds,
  })

export const fetchChatHistory = (userId: number) =>
  getJson<ChatHistoryMessage[]>(`/api/chat/history?user_id=${userId}`)

export const signup = (data: SignupData) => postJson<User>('/api/signup', data)

export const login = (email: string, password: string) =>
  postJson<User>('/api/login', { email, password })

// Mirrors password_problems() in backend/main.py so users get instant feedback;
// the backend re-checks everything.
export const passwordRules = [
  { label: 'At least 10 characters', test: (pw: string) => pw.length >= 10 },
  { label: 'An uppercase letter', test: (pw: string) => /[A-Z]/.test(pw) },
  { label: 'A number', test: (pw: string) => /\d/.test(pw) },
]

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// First sentence of the db description, for compact product cards.
export const shortDescription = (description: string) => {
  const first = description.split(/(?<=\.)\s/)[0]
  return first.length > 110 ? `${first.slice(0, 107)}…` : first
}
