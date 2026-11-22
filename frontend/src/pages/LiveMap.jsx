import L from 'leaflet'
import { Layers, LocateFixed, MapPin, Search, X } from 'lucide-react'
import { useCallback, useEffect, useRef, useState } from 'react'
import { get, post } from '../api/client'
import MapView from '../components/MapView'
import { useAsync } from '../hooks/useAsync'

const LABEL = { demo: 'Demo data, not a real stop', unverified: 'Unverified', verified: 'Verified' }
const COLOR = { demo: '#94A3B8', unverified: '#FBBF24', verified: '#34D399' }

export default function LiveMap() {
  const map = useRef(null)
  const stopLayer = useRef(L.layerGroup())
  const pins = useRef({ from: null, to: null })
  const timer = useRef(null)
  const [showStops, setShowStops] = useState(true)
  const [panel, setPanel] = useState(true)
  const [stopInfo, setStopInfo] = useState({ count: 0, hint: null, error: null })
  const [q, setQ] = useState({ from: '', to: '' })
  const [results, setResults] = useState({ field: null, items: [], error: null, busy: false })
  const [picked, setPicked] = useState({ from: null, to: null })
  const [geoMsg, setGeoMsg] = useState(null)
  const layers = useAsync(() => get('/map/layers'))

  const loadStops = useCallback(async () => {
    const m = map.current
    if (!m) return
    const b = m.getBounds()
    const bbox = [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()].map((n) => n.toFixed(5)).join(',')
    try {
      const r = await get(`/transport/stops?bbox=${bbox}&per_page=500`)
      stopLayer.current.clearLayers()
      r.items.forEach((s) => {
        L.circleMarker([s.lat, s.lng], { radius: 6, color: '#080D18', weight: 2, fillColor: COLOR[s.verification_status] || '#94A3B8', fillOpacity: 1 })
          .bindPopup(`<strong>${esc(s.name)}</strong><br>${esc(LABEL[s.verification_status] || s.verification_status)}<br>Source: ${esc(s.source || 'unknown')}${s.source_updated_at ? `<br>Updated: ${esc(s.source_updated_at)}` : ''}`)
          .addTo(stopLayer.current)
      })
      setStopInfo({ count: r.total, hint: null, error: null })
    } catch (e) {
      stopLayer.current.clearLayers()
      setStopInfo({ count: 0, hint: e.code === 'bbox_too_large' ? e.message : null, error: e.code === 'bbox_too_large' ? null : e.message })
    }
  }, [])

  const onReady = useCallback((m) => {
    map.current = m
    stopLayer.current.addTo(m)
    m.on('moveend', () => { clearTimeout(timer.current); timer.current = setTimeout(loadStops, 350) })
    loadStops()
    // Clicking the map sets the next empty point, so search is never the only way in.
    m.on('click', (e) => setPinFrom(e.latlng.lat, e.latlng.lng, 'Point on map'))
  }, [loadStops]) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!map.current) return
    showStops ? stopLayer.current.addTo(map.current) : stopLayer.current.remove()
  }, [showStops])

  const placePin = (which, p) => {
    pins.current[which]?.remove()
    pins.current[which] = L.circleMarker([p.lat, p.lng], {
      radius: 9, color: '#fff', weight: 2, fillColor: which === 'from' ? '#3B82F6' : '#22D3EE', fillOpacity: 1,
    }).addTo(map.current).bindTooltip(which === 'from' ? 'From' : 'To', { permanent: true, direction: 'top', offset: [0, -8] })
    setPicked((s) => ({ ...s, [which]: p }))
  }
  function setPinFrom(lat, lng, label) {
    const which = pins.current.from && !pins.current.to ? 'to' : !pins.current.from ? 'from' : 'to'
    placePin(which, { lat, lng, label })
    setQ((s) => ({ ...s, [which]: label }))
  }

  const search = async (field) => {
    const text = q[field].trim()
    if (text.length < 3) return setResults({ field, items: [], error: 'Type at least 3 characters.', busy: false })
    setResults({ field, items: [], error: null, busy: true })
    try {
      const r = await get(`/geocode/search?q=${encodeURIComponent(text)}`)
      setResults({ field, items: r.items, error: r.items.length ? null : 'No places found. Try a landmark or street name.', busy: false })
    } catch (e) {
      setResults({ field, items: [], error: e.message, busy: false })
    }
  }
  const choose = (field, item) => {
    placePin(field, { lat: item.lat, lng: item.lng, label: item.label })
    setQ((s) => ({ ...s, [field]: item.label.split(',').slice(0, 2).join(',') }))
    setResults({ field: null, items: [], error: null, busy: false })
    map.current.flyTo([item.lat, item.lng], 15, { duration: 0.8 })
  }
  const locate = () => {
    if (!navigator.geolocation) return setGeoMsg('Your browser does not support location.')
    setGeoMsg('Waiting for your permission…')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        // Used only in this browser tab. It is never sent to the server.
        const p = { lat: pos.coords.latitude, lng: pos.coords.longitude, label: 'My location' }
        placePin('from', p); setQ((s) => ({ ...s, from: 'My location' }))
        map.current.flyTo([p.lat, p.lng], 15); setGeoMsg(null)
      },
      (err) => setGeoMsg(err.code === 1 ? 'Location permission was denied. Search for a place instead.' : 'Could not get your location.'),
      { enableHighAccuracy: false, timeout: 10000 })
  }
  const savePlace = async (which) => {
    const p = picked[which]
    try {
      await post('/users/me/saved-places', { label: (p.label || 'Saved place').split(',')[0].slice(0, 80), lat: p.lat, lng: p.lng, address: (p.label || '').slice(0, 255) })
      setGeoMsg('Saved to your profile.')
    } catch (e) { setGeoMsg(e.message) }
  }
  const clear = (which) => {
    pins.current[which]?.remove(); pins.current[which] = null
    setPicked((s) => ({ ...s, [which]: null })); setQ((s) => ({ ...s, [which]: '' }))
  }

  return (
    <div className="relative h-full min-h-[480px]">
      <MapView onReady={onReady} className="absolute inset-0" />

      <div className="pointer-events-none absolute inset-x-0 top-0 z-[500] flex flex-col gap-2 p-3 sm:max-w-sm">
        <div className="glass pointer-events-auto p-3">
          {['from', 'to'].map((f) => (
            <div key={f} className="mb-2 last:mb-0">
              <form onSubmit={(e) => { e.preventDefault(); search(f) }} className="flex gap-2" role="search">
                <div className="relative flex-1">
                  <MapPin className={`absolute left-2.5 top-3 h-4 w-4 ${f === 'from' ? 'text-primary-soft' : 'text-accent'}`} aria-hidden />
                  <input className="input !pl-8" aria-label={f === 'from' ? 'Starting point' : 'Destination'}
                    placeholder={f === 'from' ? 'From: place or landmark' : 'To: place or landmark'}
                    value={q[f]} onChange={(e) => setQ({ ...q, [f]: e.target.value })} />
                </div>
                {picked[f]
                  ? <button type="button" className="btn btn-ghost !px-3" onClick={() => clear(f)} aria-label={`Clear ${f}`}><X className="h-4 w-4" /></button>
                  : <button className="btn btn-ghost !px-3" aria-label={`Search ${f}`}><Search className="h-4 w-4" /></button>}
              </form>
              {results.field === f && (results.busy || results.error || results.items.length > 0) && (
                <ul className="mt-1 max-h-48 overflow-y-auto rounded-lg border border-line bg-base text-sm">
                  {results.busy && <li className="p-3 text-ink-mute">Searching…</li>}
                  {results.error && <li role="alert" className="p-3 text-ink-mute">{results.error}</li>}
                  {results.items.map((it, i) => (
                    <li key={i}><button className="w-full px-3 py-2 text-left hover:bg-white/5" onClick={() => choose(f, it)}>{it.label}</button></li>
                  ))}
                </ul>
              )}
              {picked[f] && <button className="mt-1 text-xs text-accent underline" onClick={() => savePlace(f)}>Save this place</button>}
            </div>
          ))}
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button className="btn btn-ghost !py-1.5 text-xs" onClick={locate}><LocateFixed className="h-4 w-4" aria-hidden /> Use my location</button>
            <button className="btn btn-primary !py-1.5 text-xs" disabled title="Journey planning arrives in Phase 3">Plan journey</button>
          </div>
          <p className="mt-2 text-xs text-ink-mute">
            {geoMsg || 'Location is read only in your browser and only when you ask. Journey planning arrives in Phase 3.'}
          </p>
        </div>
      </div>

      <div className="absolute bottom-6 left-3 z-[500] sm:bottom-8">
        <button className="btn glass !py-2 text-sm" aria-expanded={panel} onClick={() => setPanel(!panel)}>
          <Layers className="h-4 w-4" aria-hidden /> Layers
        </button>
        {panel && (
          <div className="glass mt-2 w-72 max-w-[calc(100vw-1.5rem)] p-3">
            <label className="flex items-start gap-2 text-sm">
              <input type="checkbox" className="mt-1" checked={showStops} onChange={(e) => setShowStops(e.target.checked)} />
              <span>Transport stops
                <span className="block text-xs text-ink-mute">
                  {stopInfo.error || stopInfo.hint || (stopInfo.count
                    ? `${stopInfo.count} in view. Colour shows verification status.`
                    : 'None in this view. No stop data has been imported here yet.')}
                </span>
              </span>
            </label>
            <ul className="mt-3 space-y-2 border-t border-line pt-3">
              {(layers.data?.items || []).filter((l) => l.group !== 'transport').map((l) => (
                <li key={l.id} className="text-sm text-ink-mute">
                  <span className="text-ink">{l.label}</span>
                  <span className="block text-xs">Not available yet · Phase {l.phase}. {l.note}</span>
                </li>
              ))}
              {layers.error && <li className="text-xs text-danger">Layer list failed to load.</li>}
            </ul>
            <p className="mt-3 text-xs text-ink-mute">No flood layer is active, so an empty map does not mean roads are clear.</p>
          </div>
        )}
      </div>
    </div>
  )
}

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]))
