import { motion } from 'framer-motion'
import { Link, Navigate } from 'react-router-dom'
import MapView from '../components/MapView'
import TrustLegend from '../components/TrustLegend'
import { useAuth } from '../context/AuthContext'

export default function Landing() {
  const { user } = useAuth()
  if (user) return <Navigate to="/dashboard" replace />
  return (
    <div className="min-h-full bg-base">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <span className="font-display text-lg font-semibold">SafeRoute</span>
        <nav className="flex items-center gap-2">
          <Link to="/login" className="btn btn-ghost">Sign in</Link>
          <Link to="/register" className="btn btn-primary">Create account</Link>
        </nav>
      </header>

      <section className="relative">
        <div className="mx-auto grid max-w-6xl gap-8 px-5 pb-10 pt-6 lg:grid-cols-[1fr_1.15fr] lg:items-center">
          <div>
            <h1 className="text-4xl font-semibold leading-tight sm:text-5xl">Know the road before you leave.</h1>
            <p className="mt-4 max-w-md text-lg text-ink-mute">
              Plan public transport trips across Metro Manila and see flood and road conditions with their
              source and time, so you can judge them for yourself.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/register" className="btn btn-primary">Create a free account</Link>
              <Link to="/login" className="btn btn-ghost">Sign in</Link>
            </div>
          </div>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="relative h-[340px] overflow-hidden rounded-2xl border border-line sm:h-[420px]">
            <MapView interactive={false} className="h-full w-full" label="Preview map of Metro Manila" />
            <div className="glass absolute bottom-3 left-3 right-3 p-3 text-sm sm:right-auto sm:max-w-xs">
              Live transport and flood layers connect to real data sources as they are verified.
              Nothing on this map is simulated.
            </div>
          </motion.div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-16">
        <div className="panel p-6 sm:p-8">
          <h2 className="text-2xl font-semibold">How SafeRoute labels flood information</h2>
          <p className="mt-2 max-w-2xl text-ink-mute">
            Every flood marker says where it came from and how fresh it is. Reports expire.
            An empty map never means a dry road.
          </p>
          <div className="mt-6"><TrustLegend /></div>
        </div>
        <p className="mt-6 text-sm text-ink-mute">
          Map data &copy; OpenStreetMap contributors. SafeRoute is an information aid and does not guarantee
          the safety of any route.
        </p>
      </section>
    </div>
  )
}
