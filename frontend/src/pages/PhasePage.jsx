import { DataUnavailable } from '../components/StateViews'

export default function PhasePage({ title, phase, children }) {
  return (
    <div className="mx-auto max-w-3xl p-4 sm:p-8">
      <h1 className="text-2xl font-semibold">{title}</h1>
      <DataUnavailable title={`Not built yet (Phase ${phase})`}>{children}</DataUnavailable>
    </div>
  )
}
