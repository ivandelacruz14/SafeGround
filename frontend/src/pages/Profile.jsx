import { Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { del, get, patch, put } from '../api/client'
import Field from '../components/Field'
import { ErrorState, Loading } from '../components/StateViews'
import { useAuth } from '../context/AuthContext'
import { useAsync } from '../hooks/useAsync'

export default function Profile() {
  const { user, setUser } = useAuth()
  const prefs = useAsync(() => get('/users/me/preferences'))
  const modes = useAsync(() => get('/transport/modes'))
  const places = useAsync(() => get('/users/me/saved-places'))
  const [name, setName] = useState(user.display_name)
  const [p, setP] = useState(null)
  const [msg, setMsg] = useState(null)
  useEffect(() => { if (prefs.data) setP(prefs.data) }, [prefs.data])

  const flash = (m) => { setMsg(m); setTimeout(() => setMsg(null), 3000) }
  const saveName = async (e) => { e.preventDefault(); try { setUser(await patch('/users/me', { display_name: name })); flash('Name saved.') } catch (er) { flash(er.message) } }
  const savePrefs = async () => { try { setP(await put('/users/me/preferences', p)); flash('Preferences saved.') } catch (er) { flash(er.details ? Object.values(er.details)[0] : er.message) } }
  const toggleMode = (c) => setP({ ...p, default_mode_codes: p.default_mode_codes.includes(c) ? p.default_mode_codes.filter((x) => x !== c) : [...p.default_mode_codes, c] })
  const removePlace = async (id) => { await del(`/users/me/saved-places/${id}`).catch(() => {}); places.reload() }

  return (
    <div className="mx-auto max-w-3xl space-y-6 p-4 sm:p-8">
      <h1 className="text-2xl font-semibold">Profile</h1>
      <div role="status" aria-live="polite" className="h-5 text-sm text-accent">{msg}</div>

      <form onSubmit={saveName} className="panel space-y-4 p-5">
        <h2 className="font-medium">Account</h2>
        <Field id="name" label="Display name" value={name} onChange={(e) => setName(e.target.value)} />
        <p className="text-sm text-ink-mute">{user.email} · {user.email_verified ? 'Verified' : 'Not verified yet'}</p>
        <button className="btn btn-primary">Save name</button>
      </form>

      <section className="panel space-y-4 p-5" aria-labelledby="prefs">
        <h2 id="prefs" className="font-medium">Travel preferences</h2>
        {prefs.loading && <Loading />}
        {prefs.error && <ErrorState error={prefs.error} onRetry={prefs.reload} />}
        {p && (<>
          <fieldset>
            <legend className="mb-2 text-sm font-medium">Modes you usually take</legend>
            <div className="flex flex-wrap gap-2">
              {(modes.data?.items || []).map((m) => (
                <label key={m.code} className={`chip cursor-pointer !px-3 !py-1.5 ${p.default_mode_codes.includes(m.code) ? 'border-accent text-accent' : 'border-line text-ink-mute'}`}>
                  <input type="checkbox" className="sr-only" checked={p.default_mode_codes.includes(m.code)} onChange={() => toggleMode(m.code)} />
                  {m.name}
                </label>
              ))}
            </div>
          </fieldset>
          <Field id="walk" label="Longest walk you accept (metres)" type="number" min="100" max="5000" step="50"
            value={p.max_walk_meters} onChange={(e) => setP({ ...p, max_walk_meters: Number(e.target.value) })} />
          {[['avoid_flood_risk', 'Avoid routes with flood warnings or reports'], ['notify_flood', 'Notify me about floods on saved trips'],
            ['notify_closures', 'Notify me about road closures'], ['notify_disruptions', 'Notify me about transport disruptions']].map(([k, label]) => (
            <label key={k} className="flex items-center gap-3 text-sm">
              <input type="checkbox" checked={p[k]} onChange={(e) => setP({ ...p, [k]: e.target.checked })} /> {label}
            </label>))}
          <button className="btn btn-primary" onClick={savePrefs}>Save preferences</button>
        </>)}
      </section>

      <section className="panel p-5" aria-labelledby="places">
        <h2 id="places" className="mb-3 font-medium">Saved places</h2>
        {places.loading && <Loading />}
        {places.error && <ErrorState error={places.error} onRetry={places.reload} />}
        {places.data && places.data.items.length === 0 && (
          <p className="text-sm text-ink-mute">No saved places yet. Search for a place on the live map and choose Save this place.</p>)}
        <ul className="divide-y divide-line">
          {places.data?.items.map((pl) => (
            <li key={pl.id} className="flex items-center gap-3 py-2.5">
              <div className="min-w-0 flex-1"><p className="truncate text-sm font-medium">{pl.label}</p>
                <p className="truncate text-xs text-ink-mute">{pl.address || `${pl.lat.toFixed(4)}, ${pl.lng.toFixed(4)}`}</p></div>
              <button className="rounded-lg p-2 text-ink-mute hover:bg-white/5 hover:text-danger" aria-label={`Delete ${pl.label}`} onClick={() => removePlace(pl.id)}>
                <Trash2 className="h-4 w-4" /></button>
            </li>))}
        </ul>
      </section>
    </div>
  )
}
