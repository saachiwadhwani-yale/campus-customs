import { Link } from 'react-router-dom'
import { formatPrice } from '../api'
import { useWishlist } from '../wishlist'

export default function Wishlist() {
  const { items, remove, clear } = useWishlist()

  if (items.length === 0) {
    return (
      <div className="wishlist-empty">
        <h1>Your Wishlist</h1>
        <p className="muted">
          You haven’t saved anything yet. Tap “Save to wishlist” on a product to keep it here,
          then pull up this list when you visit our store on Broadway.
        </p>
        <Link to="/products" className="btn btn-primary">Browse products</Link>
      </div>
    )
  }

  return (
    <>
      <div className="section-head">
        <h1>Your Wishlist</h1>
        <button className="link-button" onClick={clear}>Clear wishlist</button>
      </div>

      <p className="muted wishlist-note">
        These are the items you’ve saved. Show this list to a Campus Customs associate in store,
        or open any item to see its details and stock.
      </p>

      <ul className="wishlist-list">
        {items.map((item) => (
          <li key={`${item.product_id}-${item.size ?? ''}`} className="wishlist-row">
            <Link to={`/products/${item.product_id}`} className="wishlist-thumb">
              <img src={item.image_url} alt={item.name} loading="lazy" />
            </Link>
            <div className="wishlist-info">
              <Link to={`/products/${item.product_id}`} className="wishlist-name">
                {item.name}
              </Link>
              {item.size && <span className="muted">Interested in size: {item.size}</span>}
              <span className="price">{formatPrice(item.price)}</span>
            </div>
            <button
              className="wishlist-remove"
              aria-label={`Remove ${item.name}${item.size ? ` size ${item.size}` : ''} from wishlist`}
              onClick={() => remove(item.product_id, item.size)}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </>
  )
}
