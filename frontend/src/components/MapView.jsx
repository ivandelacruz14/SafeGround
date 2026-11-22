import L from 'leaflet'
import { useEffect, useRef } from 'react'

export const METRO_MANILA = { center: [14.5995, 120.9842], zoom: 11 }
const TILE_URL = import.meta.env.VITE_TILE_URL || 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'
const ATTRIBUTION = import.meta.env.VITE_TILE_ATTRIBUTION ||
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
const TILES_DARK = import.meta.env.VITE_TILES_ARE_DARK === '1'

/** Thin Leaflet wrapper. Calls onReady(map) once; the parent owns markers and layers. */
export default function MapView({ onReady, interactive = true, className = '', label = 'Map of Metro Manila' }) {
  const el = useRef(null)
  useEffect(() => {
    const map = L.map(el.current, {
      center: METRO_MANILA.center, zoom: METRO_MANILA.zoom, zoomControl: interactive,
      dragging: interactive, scrollWheelZoom: interactive, doubleClickZoom: interactive,
      touchZoom: interactive, keyboard: interactive, boxZoom: interactive, attributionControl: true,
    })
    L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(map)
    onReady?.(map)
    return () => map.remove()
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  return <div ref={el} role="application" aria-label={label} className={`${TILES_DARK ? '' : 'map-dark-filter'} ${className}`} />
}
