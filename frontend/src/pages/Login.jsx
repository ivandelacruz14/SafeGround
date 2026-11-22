import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { post } from '../api/client'
import Field from '../components/Field'
import { useAuth } from '../context/AuthContext'

export function AuthShell({ title, children, footer }) {
  return (
    <div className="grid min-h-full place-items-center bg-base px-4 py-10">
      <div className="w-full max-w-sm">
        <Link to="/" className="mb-6 block font-display text-lg font-semibold">SafeRoute</Link>
        <div className="panel p-6">
          <h1 className="mb-5 text-2xl font-semibold">{title}</h1>
          {children}
        </div>
        <p className="mt-4 text-sm text-ink-mute">{footer}</p>
      </div>
    </div>
  )
}

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [form, setForm] = useState({ email: '', password: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [resent, setResent] = useState(false)
  if (user) return <Navigate to={loc.state?.from || '/dashboard'} replace />

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null)
    try { await login(form.email, form.password); nav(loc.state?.from || '/dashboard', { replace: true }) }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  const resend = async () => {
    if (!form.email) return setError('Enter your email first.')
    await post('/auth/resend-verification', { email: form.email }, { auth: false }).catch(() => {})
    setResent(true)
  }

  return (
    <AuthShell title="Sign in" footer={<>New to SafeRoute? <Link className="text-accent underline" to="/register">Create an account</Link></>}>
      <form onSubmit={submit} className="space-y-4" noValidate>
        {error && <p role="alert" className="rounded-lg bg-danger/10 p-3 text-sm text-danger">{error}</p>}
        <Field id="email" label="Email" type="email" autoComplete="email" required value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })} />
        <Field id="password" label="Password" type="password" autoComplete="current-password" required value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })} />
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <button type="button" onClick={resend} className="text-sm text-ink-mute underline">
          {resent ? 'If the account needs it, a new link was sent.' : 'Resend verification email'}
        </button>
      </form>
    </AuthShell>
  )
}
