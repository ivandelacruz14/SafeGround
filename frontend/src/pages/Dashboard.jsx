import { Link } from 'react-router-dom'
import { get } from '../api/client'
import { ErrorState, Loading } from '../components/StateViews'
import { useAuth } from '../context/AuthContext'
import { useAsync } from '../hooks/useAsync'

const STATUS = {
  available: ['Has data', 'text-trust-verified border-trust-verified/40'],
  no_data: ['No data imported yet', 'text-trust-unverified border-trust-unverified/40'],
  planned: ['Not built yet', 'text-ink-mute border-line'],
}

export default function Dashboard() {
  const { user } = useAuth()
  const { data, error, loading, reload } = useAsync(() => get('/map/layers'))
  return (
    <div className="mx-auto max-w-4xl space-y-6 p-4 sm:p-8">
      <div>
        <h1 className="text-2xl font-semibold">Hello, {user.display_name}</h1>
        <p className="mt-1 text-ink-mute">Here is what SafeRoute can and cannot tell you today.</p>
      </div>
      <div className="flex flex-wrap gap-3">
        <Link to="/map" className="btn btn-primary">Open live map</Link>
        <Link to="/profile" className="btn btn-ghost">Set preferences</Link>
      </div>
      <section aria-labelledby="coverage" className="panel">
        <h2 id="coverage" className="border-b border-line px-5 py-3 font-medium">Data coverage</h2>
        {loading && <Loading />}
        {error && <ErrorState error={error} onRetry={reload} />}
        {data && (
          <ul className="divide-y divide-line">
            {data.items.map((l) => {
              const [text, cls] = STATUS[l.status]
              return (
                <li key={l.id} className="flex flex-wrap items-center gap-3 px-5 py-3">
                  <div className="min-w-0 flex-1"><p className="font-medium">{l.label}</p>
                    <p className="text-sm text-ink-mute">{l.note}</p></div>
                  <span className={`chip ${cls}`}>{text}{l.phase ? ` · Phase ${l.phase}` : ''}</span>
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </div>
  )
}
