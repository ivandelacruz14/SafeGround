import { useState } from 'react'
import { Link } from 'react-router-dom'
import { post } from '../api/client'
import Field from '../components/Field'
import { AuthShell } from './Login'

export default function Register() {
  const [form, setForm] = useState({ display_name: '', email: '', password: '' })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async (e) => {
    e.preventDefault()
    setBusy(true); setError(null); setErrors({})
    try { await post('/auth/register', form, { auth: false }); setDone(true) }
    catch (err) { err.details ? setErrors(err.details) : setError(err.message) }
    finally { setBusy(false) }
  }

  if (done) {
    return (
      <AuthShell title="Check your email" footer={<Link className="text-accent underline" to="/login">Back to sign in</Link>}>
        <p className="text-sm text-ink-mute">
          If {form.email} can be registered, we sent a verification link. It expires in 24 hours.
          You can sign in now; some features need a verified email.
        </p>
      </AuthShell>
    )
  }
  return (
    <AuthShell title="Create your account" footer={<>Already registered? <Link className="text-accent underline" to="/login">Sign in</Link></>}>
      <form onSubmit={submit} className="space-y-4" noValidate>
        {error && <p role="alert" className="rounded-lg bg-danger/10 p-3 text-sm text-danger">{error}</p>}
        <Field id="name" label="Name" autoComplete="name" value={form.display_name} onChange={set('display_name')} error={errors.display_name} />
        <Field id="email" label="Email" type="email" autoComplete="email" value={form.email} onChange={set('email')} error={errors.email} />
        <Field id="password" label="Password" type="password" autoComplete="new-password" value={form.password}
          onChange={set('password')} error={errors.password} hint="At least 10 characters." />
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'Creating account…' : 'Create account'}</button>
      </form>
    </AuthShell>
  )
}
