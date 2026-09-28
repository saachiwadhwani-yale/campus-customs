import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { useWishlist } from '../wishlist'

const mainLinks = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/about', label: 'About Us' },
]

const linkClass = ({ isActive }: { isActive: boolean }) => `nav-link${isActive ? ' active' : ''}`

export default function NavBar() {
  const { user, setUser } = useAuth()
  const { count } = useWishlist()
  const navigate = useNavigate()

  function logOut() {
    setUser(null)
    navigate('/')
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">
        Campus Customs
        <span className="brand-sub">Est. 1975 · New Haven</span>
      </Link>
      <nav>
        {mainLinks.map((l) => (
          <NavLink key={l.to} to={l.to} end={l.end} className={linkClass}>
            {l.label}
          </NavLink>
        ))}
        <NavLink to="/wishlist" className={linkClass}>
          ♥ Wishlist{count > 0 && <span className="wishlist-badge">{count}</span>}
        </NavLink>
        {user ? (
          <>
            <span className="nav-user">Hi, {user.first_name || user.name}</span>
            <button className="nav-link nav-cta nav-button" onClick={logOut}>Log Out</button>
          </>
        ) : (
          <>
            <NavLink to="/login" className={linkClass}>Log In</NavLink>
            <NavLink
              to="/create-account"
              className={(s) => `${linkClass(s)} nav-cta`}
            >
              Create Account
            </NavLink>
          </>
        )}
      </nav>
    </header>
  )
}
