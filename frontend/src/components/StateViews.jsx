import { Loader2, TriangleAlert, WifiOff, DatabaseZap } from 'lucide-react'

export function Loading({ label = 'Loading' }) {
  return (
    <div role="status" className="flex items-center gap-2 p-6 text-sm text-ink-mute">
      <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> {label}
    </div>
  )
}

export function ErrorState({ error, onRetry }) {
  const offline = error?.code === 'network'
  const Icon = offline ? WifiOff : TriangleAlert
  return (
    <div role="alert" className="panel m-4 flex flex-col items-start gap-3 p-5">
      <Icon className="h-5 w-5 text-danger" aria-hidden />
      <div>
        <p className="font-medium">{offline ? 'You appear to be offline' : 'This did not load'}</p>
        <p className="mt-1 text-sm text-ink-mute">{error?.message || 'Try again in a moment.'}</p>
      </div>
      {onRetry && <button className="btn btn-ghost" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function EmptyState({ title, children, action }) {
  return (
    <div className="panel m-4 p-6 text-center">
      <p className="font-medium">{title}</p>
      {children && <p className="mx-auto mt-1 max-w-md text-sm text-ink-mute">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

/** Shown when a data source has nothing yet. Never implies the situation is safe or complete. */
export function DataUnavailable({ title = 'No data available yet', children }) {
  return (
    <div className="panel m-4 flex gap-3 p-5">
      <DatabaseZap className="mt-0.5 h-5 w-5 shrink-0 text-trust-unknown" aria-hidden />
      <div>
        <p className="font-medium">{title}</p>
        <p className="mt-1 max-w-xl text-sm text-ink-mute">{children}</p>
      </div>
    </div>
  )
}

export function OfflineBanner() {
  return (
    <div role="status" className="flex items-center gap-2 bg-amber-400/15 px-4 py-2 text-sm text-amber-200">
      <WifiOff className="h-4 w-4" aria-hidden /> You are offline. Data on screen may be out of date.
    </div>
  )
}
