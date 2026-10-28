let loading = null

export function mapsKey() {
  return import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
}

export function mapsConfigured() {
  return Boolean(mapsKey().trim())
}

/** Load Maps JavaScript API once (satellite picker + Places autocomplete). */
export function loadGoogleMaps() {
  if (typeof window !== 'undefined' && window.google?.maps) {
    return Promise.resolve(window.google.maps)
  }
  const key = mapsKey()
  if (!key) {
    return Promise.reject(new Error('VITE_GOOGLE_MAPS_API_KEY is empty'))
  }
  if (loading) return loading

  loading = new Promise((resolve, reject) => {
    const existing = document.querySelector('script[data-solar-maps]')
    if (existing) {
      existing.addEventListener('load', () => resolve(window.google.maps))
      existing.addEventListener('error', () => reject(new Error('Maps script failed')))
      return
    }
    const script = document.createElement('script')
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(key)}&libraries=places&v=weekly`
    script.async = true
    script.defer = true
    script.dataset.solarMaps = '1'
    script.onload = () => {
      if (!window.google?.maps) {
        reject(new Error('Google Maps failed to initialize'))
        return
      }
      resolve(window.google.maps)
    }
    script.onerror = () => reject(new Error('Could not load Google Maps script'))
    document.head.appendChild(script)
  })

  return loading
}
