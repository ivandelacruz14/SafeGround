import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { api, post, refreshSession, setAccessToken } from '../api/client'

const AuthContext = createContext(null)
export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let live = true
    refreshSession()
      .then((d) => live && setUser(d.user))
      .catch(() => {})
      .finally(() => live && setLoading(false))
    const onExpired = () => setUser(null)
    window.addEventListener('auth:expired', onExpired)
    return () => { live = false; window.removeEventListener('auth:expired', onExpired) }
  }, [])

  const login = useCallback(async (email, password) => {
    const d = await post('/auth/login', { email, password }, { auth: false })
    setAccessToken(d.access_token)
    setUser(d.user)
    return d.user
  }, [])

  const logout = useCallback(async () => {
    await post('/auth/logout', null, { auth: false }).catch(() => {})
    setAccessToken(null)
    setUser(null)
  }, [])

  const reload = useCallback(async () => setUser(await api('/users/me')), [])

  const value = useMemo(() => ({ user, loading, login, logout, reload, setUser }), [user, loading, login, logout, reload])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
