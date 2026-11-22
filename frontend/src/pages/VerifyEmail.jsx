import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { post } from '../api/client'
import { Loading } from '../components/StateViews'
import { AuthShell } from './Login'

export default function VerifyEmail() {
  const [params] = useSearchParams()
  const [state, setState] = useState({ status: 'loading' })
  useEffect(() => {
    const token = params.get('token')
    if (!token) return setState({ status: 'error', message: 'This link is missing its token.' })
    post('/auth/verify-email', { token }, { auth: false })
      .then(() => setState({ status: 'ok' }))
      .catch((e) => setState({ status: 'error', message: e.message }))
  }, [params])

  return (
    <AuthShell title="Email verification" footer={<Link className="text-accent underline" to="/login">Go to sign in</Link>}>
      {state.status === 'loading' && <Loading label="Verifying" />}
      {state.status === 'ok' && <p role="status" className="text-sm">Your email is verified. You can now use every feature.</p>}
      {state.status === 'error' && <p role="alert" className="text-sm text-danger">{state.message}</p>}
    </AuthShell>
  )
}
