import { useState } from 'react'
import { get, patch } from '../api/client'
import { EmptyState, ErrorState, Loading } from '../components/StateViews'
import { useAuth } from '../context/AuthContext'
import { useAsync } from '../hooks/useAsync'

export function Pager({ data, page, setPage }) {
  if (!data || data.pages <= 1) return null
  return (
    <div className="flex items-center justify-between border-t border-line px-4 py-3 text-sm">
      <span className="text-ink-mute">Page {page} of {data.pages} · {data.total} total</span>
      <div className="flex gap-2">
        <button className="btn btn-ghost !py-1.5" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
        <button className="btn btn-ghost !py-1.5" disabled={page >= data.pages} onClick={() => setPage(page + 1)}>Next</button>
      </div>
    </div>
  )
}

export default function AdminUsers() {
  const { user: me } = useAuth()
  const [q, setQ] = useState('')
  const [term, setTerm] = useState('')
  const [role, setRole] = useState('')
  const [page, setPage] = useState(1)
  const [err, setErr] = useState(null)
  const { data, error, loading, reload } = useAsync(
    () => get(`/admin/users?page=${page}&per_page=20&q=${encodeURIComponent(term)}&role=${role}`), [page, term, role])

  const update = async (u, body) => {
    setErr(null)
    try { await patch(`/admin/users/${u.id}`, body); reload() } catch (e) { setErr(e.message) }
  }

  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4 sm:p-8">
      <h1 className="text-2xl font-semibold">Users</h1>
      <form className="flex flex-wrap gap-2" onSubmit={(e) => { e.preventDefault(); setPage(1); setTerm(q) }} role="search">
        <input className="input max-w-xs" aria-label="Search users" placeholder="Search name or email" value={q} onChange={(e) => setQ(e.target.value)} />
        <select className="input max-w-[10rem]" aria-label="Filter by role" value={role} onChange={(e) => { setPage(1); setRole(e.target.value) }}>
          <option value="">All roles</option><option value="user">User</option><option value="moderator">Moderator</option><option value="admin">Admin</option>
        </select>
        <button className="btn btn-ghost">Search</button>
      </form>
      {err && <p role="alert" className="text-sm text-danger">{err}</p>}
      <div className="panel overflow-x-auto">
        {loading && <Loading />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && data.items.length === 0 && <EmptyState title="No users match">Try a different search or role filter.</EmptyState>}
        {data && data.items.length > 0 && (
          <table className="w-full min-w-[640px] text-left text-sm">
            <thead className="border-b border-line text-ink-mute"><tr>
              <th className="px-4 py-3 font-medium">User</th><th className="px-4 py-3 font-medium">Role</th>
              <th className="px-4 py-3 font-medium">Status</th><th className="px-4 py-3 font-medium">Verified</th></tr></thead>
            <tbody className="divide-y divide-line">
              {data.items.map((u) => (
                <tr key={u.id}>
                  <td className="px-4 py-3"><p className="font-medium">{u.display_name}</p><p className="text-xs text-ink-mute">{u.email}</p></td>
                  <td className="px-4 py-3">
                    <select className="input !py-1.5" aria-label={`Role for ${u.email}`} value={u.role} disabled={u.id === me.id}
                      onChange={(e) => update(u, { role: e.target.value })}>
                      <option value="user">User</option><option value="moderator">Moderator</option><option value="admin">Admin</option></select></td>
                  <td className="px-4 py-3">
                    <button className={`chip ${u.status === 'active' ? 'border-trust-verified/40 text-trust-verified' : 'border-danger/40 text-danger'}`}
                      disabled={u.id === me.id} onClick={() => update(u, { status: u.status === 'active' ? 'suspended' : 'active' })}
                      aria-label={`${u.status === 'active' ? 'Suspend' : 'Reactivate'} ${u.email}`}>{u.status}</button></td>
                  <td className="px-4 py-3 text-ink-mute">{u.email_verified ? 'Yes' : 'No'}</td>
                </tr>))}
            </tbody>
          </table>)}
        <Pager data={data} page={page} setPage={setPage} />
      </div>
    </div>
  )
}
