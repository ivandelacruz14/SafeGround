import { useState } from 'react'
import { get } from '../api/client'
import { EmptyState, ErrorState, Loading } from '../components/StateViews'
import { useAsync } from '../hooks/useAsync'
import { Pager } from './AdminUsers'

export default function AdminAudit() {
  const [page, setPage] = useState(1)
  const { data, error, loading, reload } = useAsync(() => get(`/admin/audit-logs?page=${page}&per_page=50`), [page])
  return (
    <div className="mx-auto max-w-5xl space-y-4 p-4 sm:p-8">
      <h1 className="text-2xl font-semibold">Audit logs</h1>
      <div className="panel overflow-x-auto">
        {loading && <Loading />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && data.items.length === 0 && <EmptyState title="No activity recorded yet" />}
        {data && data.items.length > 0 && (
          <table className="w-full min-w-[680px] text-left text-sm">
            <thead className="border-b border-line text-ink-mute"><tr>
              <th className="px-4 py-3 font-medium">Time (UTC)</th><th className="px-4 py-3 font-medium">Actor</th>
              <th className="px-4 py-3 font-medium">Action</th><th className="px-4 py-3 font-medium">Target</th></tr></thead>
            <tbody className="divide-y divide-line">
              {data.items.map((a) => (
                <tr key={a.id}>
                  <td className="whitespace-nowrap px-4 py-2.5 text-ink-mute">{a.created_at.replace('T', ' ').slice(0, 19)}</td>
                  <td className="px-4 py-2.5">{a.actor || 'System'}</td>
                  <td className="px-4 py-2.5">{a.action}</td>
                  <td className="px-4 py-2.5 text-ink-mute">{a.entity_type ? `${a.entity_type} #${a.entity_id}` : ''}</td>
                </tr>))}
            </tbody>
          </table>)}
        <Pager data={data} page={page} setPage={setPage} />
      </div>
    </div>
  )
}
