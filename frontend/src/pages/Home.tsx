import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchProducts, formatPrice, type Product } from '../api'

export default function Home() {
  const [newProducts, setNewProducts] = useState<Product[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setNewProducts(all.filter((p) => p.total_stock > 0).slice(0, 12)))
      .catch(() => setNewProducts([]))
  }, [])

  // Duplicate the list so the marquee can scroll seamlessly.
  const tickerItems = [...newProducts, ...newProducts]

  return (
    <>
      <section className="hero window">
        <div className="window-bar">
          <span className="window-dots" aria-hidden="true">
            <i /><i /><i />
          </span>
          <span className="window-title">★ welcome.html — Campus Customs ★</span>
          <span className="window-x" aria-hidden="true">×</span>
        </div>
        <div className="window-body">
          <div className="hero-stickers" aria-hidden="true">
            <span className="sticker sticker-star s1">★ Est.<br />1975 ★</span>
            <span className="sticker sticker-holo s2">✦ 100% Yale ✦</span>
            <span className="sticker sticker-electric s3">☆ New Haven ☆</span>
          </div>
          <p className="eyebrow">Yale gear on Broadway since 1975</p>
          <h1 className="chrome-text">Bulldog pride, made right across from campus.</h1>
          <p className="hero-sub">
            Whether you’re moving into your residential college, cheering at The Game, or picking
            up a gift for a proud Yale parent, our family-run shop has the sweatshirts, tees and
            keepsakes to show where you belong.
          </p>
          <div className="hero-actions">
            <Link to="/products" className="btn btn-primary">Shop Products ✦</Link>
            <Link to="/about" className="btn btn-outline">Our Story</Link>
          </div>
        </div>
      </section>

      {newProducts.length > 0 && (
        <div className="ticker" role="region" aria-label="New products">
          <span className="ticker-label">★ New ★</span>
          <div className="ticker-viewport">
            <div className="ticker-track">
              {tickerItems.map((p, i) => (
                <Link key={`${p.product_id}-${i}`} to={`/products/${p.product_id}`} className="ticker-item">
                  <img src={p.image_url} alt="" aria-hidden="true" />
                  <span>{p.name}</span>
                  <span className="ticker-price">{formatPrice(p.price)}</span>
                  <span className="ticker-sep" aria-hidden="true">✦</span>
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      <section className="info-grid">
        <div className="info-card">
          <h3>Something for Every Bulldog</h3>
          <p>
            Browse layers and tees for each residential college, graduate school and varsity
            team, along with small souvenirs and gifts to take home.
          </p>
        </div>
        <div className="info-card">
          <h3>Custom Orders</h3>
          <p>
            Planning a team, club or event? We print and embroider on-site and can help with
            the artwork too, so your design goes from idea to finished shirt in one place.
          </p>
        </div>
        <div className="info-card">
          <h3>Visit the Store</h3>
          <p>
            57 Broadway, New Haven, CT 06511<br />
            Mon–Sat 9:30 AM – 9:00 PM<br />
            Sun 10:00 AM – 6:00 PM
          </p>
        </div>
      </section>
    </>
  )
}
