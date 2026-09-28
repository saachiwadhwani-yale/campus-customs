import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { passwordRules, signup } from '../api'
import { useAuth } from '../auth'

export default function CreateAccount() {
  const { setUser } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (field: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  const rulesMet = passwordRules.every((r) => r.test(form.password))
  const passwordsMatch = form.password === form.confirm_password

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!rulesMet) return setError('Password does not meet the requirements below.')
    if (!passwordsMatch) return setError('Passwords do not match.')
    setSubmitting(true)
    try {
      // New accounts are logged in right away
      setUser(await signup(form))
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-card">
      <h1>Create Account</h1>
      <form onSubmit={handleSubmit}>
        <div className="form-row">
          <label>
            First name
            <input value={form.first_name} onChange={update('first_name')} required autoComplete="given-name" />
          </label>
          <label>
            Last name
            <input value={form.last_name} onChange={update('last_name')} required autoComplete="family-name" />
          </label>
        </div>
        <label>
          Email
          <input type="email" value={form.email} onChange={update('email')} required autoComplete="email" />
        </label>
        <label>
          Password
          <input type="password" value={form.password} onChange={update('password')} required autoComplete="new-password" />
        </label>
        <ul className="pw-rules">
          {passwordRules.map((r) => (
            <li key={r.label} className={r.test(form.password) ? 'met' : ''}>
              {r.test(form.password) ? '✓' : '○'} {r.label}
            </li>
          ))}
        </ul>
        <label>
          Confirm password
          <input type="password" value={form.confirm_password} onChange={update('confirm_password')} required autoComplete="new-password" />
        </label>
        {form.confirm_password && !passwordsMatch && (
          <p className="field-hint">Passwords don’t match yet.</p>
        )}
        {error && <p className="form-error" role="alert">{error}</p>}
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Creating account…' : 'Create Account'}
        </button>
      </form>
      <p className="muted">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </div>
  )
}
