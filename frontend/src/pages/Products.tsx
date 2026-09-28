import { useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchProducts, type Product } from '../api'
import ProductCard from '../components/ProductCard'
import { usePageContext } from '../pageContext'

type SortKey = 'featured' | 'price-asc' | 'price-desc' | 'color' | 'type'

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'featured', label: 'Featured' },
  { value: 'price-asc', label: 'Price: Low to High' },
  { value: 'price-desc', label: 'Price: High to Low' },
  { value: 'color', label: 'Color' },
  { value: 'type', label: 'Item type' },
]

export default function Products() {
  const [products, setProducts] = useState<Product[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [sort, setSort] = useState<SortKey>('featured')
  const [searchParams] = useSearchParams()
  const { setProductIds } = usePageContext()

  useEffect(() => {
    fetchProducts()
      .then(setProducts)
      .catch((e: Error) => setError(e.message))
  }, [])

  // The chat assistant links here with ?ids=a,b,c&q=<question> to filter the
  // grid down to what it found. Order is preserved from the ids list.
  const idsParam = searchParams.get('ids')
  const question = searchParams.get('q')
  const filterIds = useMemo(
    () => (idsParam ? idsParam.split(',').filter(Boolean) : null),
    [idsParam],
  )

  const filtered = useMemo(() => {
    if (!products) return []
    if (!filterIds) return products
    const byId = new Map(products.map((p) => [p.product_id, p]))
    return filterIds.map((id) => byId.get(id)).filter((p): p is Product => Boolean(p))
  }, [products, filterIds])

  // Sort a copy so the underlying data / chat order is preserved. "Featured"
  // keeps the incoming order (catalogue order, or the chat's best-first ranking).
  const visible = useMemo(() => {
    const items = [...filtered]
    switch (sort) {
      case 'price-asc':
        return items.sort((a, b) => a.price - b.price)
      case 'price-desc':
        return items.sort((a, b) => b.price - a.price)
      case 'color':
        return items.sort((a, b) =>
          (a.colors[0] ?? '').localeCompare(b.colors[0] ?? '') ||
          a.name.localeCompare(b.name),
        )
      case 'type':
        return items.sort((a, b) =>
          a.garment_type.localeCompare(b.garment_type) || a.name.localeCompare(b.name),
        )
      default:
        return items
    }
  }, [filtered, sort])

  // Tell the chat agent which products are on screen. When filtered (a search),
  // that's the result set; when showing the whole catalogue, there's no specific
  // context to pass, so leave it empty.
  useEffect(() => {
    setProductIds(filterIds ? visible.map((p) => p.product_id) : [])
    return () => setProductIds([])
  }, [filterIds, visible, setProductIds])

  if (error) return <p className="error">Couldn’t load products: {error}</p>
  if (!products) return <p className="muted">Loading products…</p>

  return (
    <>
      <div className="section-head">
        <h1>Products</h1>
        <div className="products-controls">
          <span className="muted">{visible.length} items</span>
          <label className="sort-control">
            Sort by
            <select value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>
              {SORT_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>{o.label}</option>
              ))}
            </select>
          </label>
        </div>
      </div>

      {filterIds && (
        <div className="filter-banner">
          <span>
            Showing chat results
            {question ? (
              <>
                {' '}for “<strong>{question}</strong>”
              </>
            ) : null}
            .
          </span>
          <Link to="/products" className="filter-clear">Show all products</Link>
        </div>
      )}

      {visible.length === 0 ? (
        <p className="muted">
          No matching products.{' '}
          <Link to="/products">Show all products</Link>
        </p>
      ) : (
        <div className="product-grid">
          {visible.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      )}
    </>
  )
}
