export const TRUST_LEVELS = [
  { id: 'official', label: 'Official warning', text: 'Issued by a government agency. Shown with its source and issue time.', color: 'bg-trust-official' },
  { id: 'verified', label: 'Verified report', text: 'A community report a moderator has confirmed. Expires after a set time.', color: 'bg-trust-verified' },
  { id: 'unverified', label: 'Unverified report', text: 'Submitted by a commuter, not yet checked. Treat with caution.', color: 'bg-trust-unverified' },
  { id: 'historical', label: 'Flood-prone area', text: 'Flooded before. Says nothing about right now.', color: 'bg-trust-historical' },
  { id: 'unknown', label: 'No information', text: 'No report does not mean the road is safe.', color: 'bg-trust-unknown' },
]

export default function TrustLegend({ compact = false }) {
  return (
    <ul className={compact ? 'space-y-2' : 'grid gap-3 sm:grid-cols-2'}>
      {TRUST_LEVELS.map((t) => (
        <li key={t.id} className="flex gap-3">
          <span className={`mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full ${t.color}`} aria-hidden />
          <span className="text-sm"><span className="font-medium">{t.label}.</span>{' '}
            <span className="text-ink-mute">{t.text}</span></span>
        </li>
      ))}
    </ul>
  )
}
