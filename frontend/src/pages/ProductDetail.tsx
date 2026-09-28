import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type Product } from '../api'
import { usePageContext } from '../pageContext'
import { useWishlist } from '../wishlist'

export default function ProductDetail() {
  const { productId } = useParams<{ productId: string }>()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedSize, setSelectedSize] = useState<string | null>(null)
  const { setProductIds } = usePageContext()
  const { has, toggle } = useWishlist()

  useEffect(() => {
    if (!productId) return
    setProduct(null)
    setError(null)
    fetchProduct(productId)
      .then((p) => {
        setProduct(p)
        // Preselect the first size that's in stock
        setSelectedSize(p.inventory.find((s) => s.quantity > 0)?.size ?? null)
      })
      .catch((e: Error) => setError(e.message))
  }, [productId])

  // Let the chat agent know the customer is viewing this one product.
  useEffect(() => {
    setProductIds(productId ? [productId] : [])
    return () => setProductIds([])
  }, [productId, setProductIds])

  if (error) return <p className="error">Couldn’t load product: {error}</p>
  if (!product) return <p className="muted">Loading…</p>

  const selected = product.inventory.find((s) => s.size === selectedSize)
  const saved = has(product.product_id, selectedSize ?? undefined)

  function handleToggleWishlist() {
    if (!product) return
    toggle({
      product_id: product.product_id,
      name: product.name,
      price: product.price,
      image_url: product.image_url,
      size: selectedSize ?? undefined,
    })
  }

  return (
    <div className="detail">
      <Link to="/products" className="back-link">← Back to products</Link>
      <h1 className="detail-title">{product.name}</h1>

      <div className="detail-body">
        <div className="detail-image">
          <img src={product.image_url} alt={product.name} />
        </div>

        <div className="detail-info">
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-type">{product.garment_type}</p>
          <p>{product.description}</p>

          {product.colors.length > 0 && (
            <p className="muted">Colors: {product.colors.join(', ')}</p>
          )}

          <h3>Size</h3>
          <div className="size-options">
            {product.inventory.map((s) => (
              <button
                key={s.size}
                className={`size-btn${s.size === selectedSize ? ' selected' : ''}${s.quantity === 0 ? ' sold-out' : ''}`}
                onClick={() => setSelectedSize(s.size)}
                aria-pressed={s.size === selectedSize}
              >
                {s.size}
              </button>
            ))}
          </div>

          <p className="stock-line">
            {selected
              ? selected.quantity > 0
                ? `${selected.quantity} in stock in size ${selected.size}`
                : `Size ${selected.size} is sold out`
              : 'Select a size'}
          </p>

          <button
            className={`btn add-to-cart${saved ? ' btn-outline' : ' btn-primary'}`}
            onClick={handleToggleWishlist}
            aria-pressed={saved}
          >
            {saved
              ? `♥ Saved${selectedSize ? ` (${selectedSize})` : ''} — remove`
              : `♡ Save${selectedSize ? ` size ${selectedSize}` : ''} to wishlist`}
          </button>

          <table className="stock-table">
            <thead>
              <tr>
                {product.inventory.map((s) => <th key={s.size}>{s.size}</th>)}
              </tr>
            </thead>
            <tbody>
              <tr>
                {product.inventory.map((s) => (
                  <td key={s.size} className={s.quantity === 0 ? 'zero' : ''}>{s.quantity}</td>
                ))}
              </tr>
            </tbody>
          </table>
          <p className="muted">Total available: {product.total_stock}</p>
        </div>
      </div>
    </div>
  )
}
