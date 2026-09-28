import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { fetchChatHistory, formatPrice, sendChat, type ChatTurn, type ProductCard } from '../api'
import { useAuth } from '../auth'
import { usePageContext } from '../pageContext'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ProductCard[]
}

const GREETING: Message = {
  role: 'assistant',
  content: 'Woof! I’m Handsome Dan, Yale’s bulldog. What are we shopping for today?',
}

const DAN = '🐶'

export default function ChatPanel() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const bottomRef = useRef<HTMLDivElement>(null)
  const navigate = useNavigate()
  const { user } = useAuth()
  const { productIds } = usePageContext()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, open])

  // Restore saved history when a customer is logged in; reset to a plain
  // greeting for guests or after logout.
  useEffect(() => {
    if (!user) {
      setMessages([GREETING])
      return
    }
    let cancelled = false
    fetchChatHistory(user.id)
      .then((saved) => {
        if (cancelled) return
        const restored: Message[] = saved.map((m) => ({
          role: m.role,
          content: m.content,
          products: m.products,
        }))
        const first = `Woof, welcome back ${user.first_name || user.name}! What can I fetch for you today?`
        setMessages([{ role: 'assistant', content: first }, ...restored])
      })
      .catch(() => {
        if (!cancelled) setMessages([GREETING])
      })
    return () => {
      cancelled = true
    }
  }, [user])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const text = input.trim()
    if (!text || sending) return

    // Send the prior turns so the agent has conversation context
    const history: ChatTurn[] = messages
      .filter((m) => m.content)
      .map((m) => ({ role: m.role, content: m.content }))

    setMessages((m) => [...m, { role: 'user', content: text }])
    setInput('')
    setSending(true)
    try {
      const res = await sendChat(text, history, user?.id ?? null, productIds)
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: res.reply, products: res.products },
      ])
      // Dynamically update the shop page to match the question. When the agent
      // found products, filter the Products page down to them; otherwise clear
      // any previous filter so the page reflects the latest question.
      if (res.products.length > 0) {
        const ids = res.products.map((p) => p.product_id).join(',')
        navigate(`/products?ids=${ids}&q=${encodeURIComponent(text)}`)
      }
    } catch {
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: 'Sorry, I couldn’t reach the server. Please try again.' },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="chat-root">
      {open && (
        <div className="chat-panel" role="dialog" aria-label="Chat with Handsome Dan">
          <div className="chat-header">
            <span className="dan-avatar" aria-hidden="true">{DAN}</span>
            <span className="dan-title">
              <span className="dan-name">Handsome Dan</span>
              <span className="dan-sub">Yale’s mascot · Campus Customs</span>
              <span className="dan-status">online &amp; ready to fetch</span>
            </span>
            <button className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">×</button>
          </div>
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-turn ${m.role}`}>
                <div className="chat-bubble-row">
                  {m.role === 'assistant' && (
                    <span className="msg-avatar" aria-hidden="true">{DAN}</span>
                  )}
                  <div className={`chat-msg ${m.role}`}>{m.content}</div>
                </div>
                {m.products && m.products.length > 0 && (
                  <div className="chat-cards">
                    {m.products.map((p) => (
                      <Link
                        key={p.product_id}
                        to={`/products/${p.product_id}`}
                        className="chat-card"
                        onClick={() => setOpen(false)}
                      >
                        <img src={p.image_url} alt={p.name} loading="lazy" />
                        <div className="chat-card-body">
                          <span className="chat-card-name">{p.name}</span>
                          <span className="chat-card-price">{formatPrice(p.price)}</span>
                          <span className="chat-card-stock">
                            {p.in_stock ? `Sizes: ${p.available_sizes.join(', ')}` : 'Out of stock'}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-turn assistant">
                <div className="chat-bubble-row">
                  <span className="msg-avatar" aria-hidden="true">{DAN}</span>
                  <div className="chat-msg assistant typing">Handsome Dan is sniffing around…</div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>
          <form className="chat-input" onSubmit={handleSubmit}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Handsome Dan about gear, sizes…"
              aria-label="Chat message"
            />
            <button type="submit" disabled={sending || !input.trim()}>
              Send
            </button>
          </form>
        </div>
      )}
      <button
        className="chat-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? 'Close chat' : 'Chat with Handsome Dan'}
      >
        <span className="dan-face" aria-hidden="true">{open ? '×' : DAN}</span>
        {!open && <span>Chat with Handsome Dan</span>}
      </button>
    </div>
  )
}
