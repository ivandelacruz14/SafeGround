const BASE = import.meta.env.VITE_API_BASE || '/api/v1'
let accessToken = null
let refreshing = null

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message)
    this.status = status
    this.code = code
    this.details = details
  }
}

const csrf = () => {
  const m = document.cookie.match(/(?:^|; )csrf_refresh_token=([^;]+)/)
  return m ? decodeURIComponent(m[1]) : ''
}

async function send(path, { method = 'GET', body, auth = true, headers = {} } = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      credentials: 'include',
      headers: {
        ...(body ? { 'Content-Type': 'application/json' } : {}),
        ...(auth && accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new ApiError(0, 'network', 'Cannot reach the SafeRoute server. Check your connection and try again.')
  }
  if (res.status === 204) return null
  const data = await res.json().catch(() => null)
  if (!res.ok) {
    const e = data?.error
    throw new ApiError(res.status, e?.code || 'http_error', e?.message || 'Request failed.', e?.details)
  }
  return data
}

export function setAccessToken(t) { accessToken = t }

export function refreshSession() {
  // Single flight: concurrent 401s share one refresh call.
  refreshing ||= send('/auth/refresh', { method: 'POST', auth: false, headers: { 'X-CSRF-TOKEN': csrf() } })
    .then((d) => { accessToken = d.access_token; return d })
    .finally(() => { refreshing = null })
  return refreshing
}

export async function api(path, opts = {}) {
  try {
    return await send(path, opts)
  } catch (e) {
    const expired = e.status === 401 && ['token_expired', 'unauthorized', 'token_invalid'].includes(e.code)
    if (expired && opts.auth !== false && path !== '/auth/refresh') {
      try { await refreshSession() } catch {
        accessToken = null
        window.dispatchEvent(new Event('auth:expired'))
        throw e
      }
      return send(path, opts)
    }
    throw e
  }
}

export const get = (p) => api(p)
export const post = (p, body, opts) => api(p, { method: 'POST', body, ...opts })
export const put = (p, body) => api(p, { method: 'PUT', body })
export const patch = (p, body) => api(p, { method: 'PATCH', body })
export const del = (p) => api(p, { method: 'DELETE' })
