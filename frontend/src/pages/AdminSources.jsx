import { get } from '../api/client'
import { ErrorState, Loading } from '../components/StateViews'
import { useAsync } from '../hooks/useAsync'

const STATUS = {
  verified_access: ['Access verified', 'border-trust-verified/40 text-trust-verified'],
  unverified: ['Not verified', 'border-trust-unverified/40 text-trust-unverified'],
  manual_only: ['Manual entry only', 'border-line text-ink-mute'],
  unavailable: ['Unavailable', 'border-danger/40 text-danger'],
}

export default function AdminSources() {
  const { data, error, loading, reload } = useAsync(() => get('/admin/data-sources'))
  return (
    <div className="mx-auto max-w-4xl space-y-4 p-4 sm:p-8">
      <h1 className="text-2xl font-semibold">Data sources</h1>
      <p className="max-w-2xl text-sm text-ink-mute">
        Each source records what has actually been verified. Nothing here is assumed to have a working API or a usable licence until someone has checked.
      </p>
      {loading && <Loading />}
      {error && <ErrorState error={error} onRetry={reload} />}
      <ul className="space-y-3">
        {data?.items.map((s) => {
          const [text, cls] = STATUS[s.access_status] || STATUS.unverified
          return (
            <li key={s.id} className="panel p-4">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="flex-1 font-medium">{s.name}</h2><span className={`chip ${cls}`}>{text}</span>
              </div>
              <p className="mt-1 text-sm text-ink-mute">{s.notes}</p>
              <p className="mt-2 text-xs text-ink-mute">
                Licence: {s.license || 'not recorded'} · Last checked: {s.last_checked_at || 'never'} · Last data update: {s.last_updated_at || 'none'}
              </p>
            </li>)
        })}
      </ul>
    </div>
  )
}
