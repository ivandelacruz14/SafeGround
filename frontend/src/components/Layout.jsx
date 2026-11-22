import { AnimatePresence, motion } from 'framer-motion'
import {
  Bell, Bookmark, Bot, Database, Layers, LayoutDashboard, LogOut, Map as MapIcon, Megaphone,
  Menu, Receipt, Route, ScrollText, ShieldCheck, Users, Waves, X, BarChart3, Bus,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useOnline } from '../hooks/useOnline'
import { OfflineBanner } from './StateViews'

const NAV = [
  { group: 'Plan', items: [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/map', label: 'Live map', icon: MapIcon },
    { to: '/planner', label: 'Journey planner', icon: Route, phase: 3 },
    { to: '/transport', label: 'Transport finder', icon: Bus, phase: 2 },
  ] },
  { group: 'Safety', items: [
    { to: '/flood', label: 'Flood monitoring', icon: Waves, phase: 4 },
    { to: '/reports', label: 'Community reports', icon: Megaphone, phase: 4 },
  ] },
  { group: 'You', items: [
    { to: '/assistant', label: 'Travel assistant', icon: Bot, phase: 5 },
    { to: '/trips', label: 'Saved trips', icon: Bookmark, phase: 3 },
    { to: '/notifications', label: 'Notifications', icon: Bell, phase: 5 },
    { to: '/profile', label: 'Profile', icon: ShieldCheck },
  ] },
  { group: 'Admin', admin: true, items: [
    { to: '/admin/users', label: 'Users', icon: Users },
    { to: '/admin/sources', label: 'Data sources', icon: Database },
    { to: '/admin/audit', label: 'Audit logs', icon: ScrollText },
    { to: '/admin/transport', label: 'Transport', icon: Layers, phase: 2 },
    { to: '/admin/fares', label: 'Fares', icon: Receipt, phase: 2 },
    { to: '/admin/moderation', label: 'Report moderation', icon: Megaphone, phase: 4 },
    { to: '/admin/analytics', label: 'Analytics', icon: BarChart3, phase: 6 },
  ] },
]

function Nav({ onNavigate }) {
  const { user } = useAuth()
  const isAdmin = user?.role === 'admin'
  const isMod = user?.role === 'moderator'
  return (
    <nav aria-label="Main" className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
      {NAV.filter((g) => !g.admin || isAdmin || isMod).map((g) => (
        <div key={g.group}>
          <p className="px-3 pb-1 text-xs font-medium text-ink-mute">{g.group}</p>
          {g.items.filter((i) => isAdmin || !g.admin || i.to === '/admin/sources').map(({ to, label, icon: Icon, phase }) => (
            <NavLink key={to} to={to} onClick={onNavigate}
              className={({ isActive }) => `flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors ${
                isActive ? 'bg-primary/15 text-white' : 'text-ink-mute hover:bg-white/5 hover:text-ink'}`}>
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              <span className="flex-1">{label}</span>
              {phase && <span className="text-[11px] text-ink-mute">Phase {phase}</span>}
            </NavLink>
          ))}
        </div>
      ))}
    </nav>
  )
}

function Brand() {
  return (
    <div className="flex items-center gap-2 px-5 py-4 font-display text-lg font-semibold">
      <span className="grid h-7 w-7 place-items-center rounded-lg bg-gradient-to-br from-primary to-accent text-base" aria-hidden>
        <Route className="h-4 w-4 text-base" />
      </span>
      SafeRoute
    </div>
  )
}

export default function Layout() {
  const { user, logout } = useAuth()
  const online = useOnline()
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const { pathname } = useLocation()
  useEffect(() => setOpen(false), [pathname])

  return (
    <div className="flex h-full">
      <aside className="hidden w-64 shrink-0 flex-col border-r border-line bg-side lg:flex">
        <Brand />
        <Nav />
      </aside>

      <AnimatePresence>
        {open && (
          <>
            <motion.div className="fixed inset-0 z-40 bg-black/60 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              exit={{ opacity: 0 }} onClick={() => setOpen(false)} aria-hidden />
            <motion.aside className="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-line bg-side lg:hidden"
              initial={{ x: -288 }} animate={{ x: 0 }} exit={{ x: -288 }} transition={{ type: 'tween', duration: 0.2 }}
              aria-label="Menu">
              <div className="flex items-center justify-between pr-3"><Brand />
                <button className="rounded-lg p-2 hover:bg-white/5" onClick={() => setOpen(false)} aria-label="Close menu"><X className="h-5 w-5" /></button>
              </div>
              <Nav onNavigate={() => setOpen(false)} />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center gap-3 border-b border-line bg-side/60 px-4 py-2.5">
          <button className="rounded-lg p-2 hover:bg-white/5 lg:hidden" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1" />
          <div className="text-right text-sm leading-tight">
            <p className="font-medium">{user?.display_name}</p>
            {!user?.email_verified && <p className="text-xs text-amber-300">Email not verified</p>}
          </div>
          <button className="btn btn-ghost !px-3" onClick={async () => { await logout(); nav('/') }}>
            <LogOut className="h-4 w-4" aria-hidden /> Sign out
          </button>
        </header>
        {!online && <OfflineBanner />}
        <main className="min-h-0 flex-1 overflow-y-auto"><Outlet /></main>
      </div>
    </div>
  )
}
