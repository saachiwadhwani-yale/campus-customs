import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'

export interface WishlistItem {
  product_id: string
  name: string
  price: number
  image_url: string
  size?: string // the size the customer was interested in, if they picked one
}

interface WishlistContextValue {
  items: WishlistItem[]
  count: number
  has: (productId: string, size?: string) => boolean
  toggle: (item: WishlistItem) => void
  remove: (productId: string, size?: string) => void
  clear: () => void
}

// A wishlist entry is unique per product AND size, so a Small and a Medium of the
// same item are two separate saved entries.
const sameEntry = (a: WishlistItem, b: { product_id: string; size?: string }) =>
  a.product_id === b.product_id && a.size === b.size

const WishlistContext = createContext<WishlistContextValue | null>(null)
const STORAGE_KEY = 'cc_wishlist'

export function WishlistProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<WishlistItem[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    return saved ? (JSON.parse(saved) as WishlistItem[]) : []
  })

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  }, [items])

  const has = (productId: string, size?: string) =>
    items.some((i) => sameEntry(i, { product_id: productId, size }))

  function toggle(item: WishlistItem) {
    // Toggle this exact product+size: saving the same size again removes it, but a
    // different size of the same product is added as its own entry.
    setItems((prev) =>
      prev.some((i) => sameEntry(i, item))
        ? prev.filter((i) => !sameEntry(i, item))
        : [...prev, item],
    )
  }

  function remove(productId: string, size?: string) {
    setItems((prev) => prev.filter((i) => !sameEntry(i, { product_id: productId, size })))
  }

  function clear() {
    setItems([])
  }

  return (
    <WishlistContext.Provider value={{ items, count: items.length, has, toggle, remove, clear }}>
      {children}
    </WishlistContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useWishlist() {
  const ctx = useContext(WishlistContext)
  if (!ctx) throw new Error('useWishlist must be used inside WishlistProvider')
  return ctx
}
