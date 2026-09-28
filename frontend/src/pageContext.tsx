import { createContext, useContext, useState, type ReactNode } from 'react'

interface PageContextValue {
  // product_ids currently shown on the page (search results or a viewed product)
  productIds: string[]
  setProductIds: (ids: string[]) => void
}

const PageContext = createContext<PageContextValue | null>(null)

export function PageProvider({ children }: { children: ReactNode }) {
  const [productIds, setProductIds] = useState<string[]>([])
  return (
    <PageContext.Provider value={{ productIds, setProductIds }}>
      {children}
    </PageContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePageContext() {
  const ctx = useContext(PageContext)
  if (!ctx) throw new Error('usePageContext must be used inside PageProvider')
  return ctx
}
