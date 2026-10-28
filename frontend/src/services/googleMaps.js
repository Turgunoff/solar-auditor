let loading = null

export function mapsKey() {
  return import.meta.env.VITE_GOOGLE_MAPS_API_KEY || ''
}

export function mapsConfigured() {
  return Boolean(mapsKey().trim())
}

/** Set by Google Maps JS API when the key is rejected (referrer, quota, API off). */
function mapsAuthMessage() {
  if (typeof window === 'undefined') return ''
  return window.__solarMapsAuthError || ''
}

/** Load Maps JavaScript API once (satellite picker + Places autocomplete). */
export function loadGoogleMaps(onAuthFailure) {
  if (typeof window !== 'undefined' && window.google?.maps) {
    return Promise.resolve(window.google.maps)
  }
  const key = mapsKey()
  if (!key) {
    return Promise.reject(new Error('VITE_GOOGLE_MAPS_API_KEY is empty'))
  }
  if (loading) return loading

  if (typeof window !== 'undefined' && !window.gm_authFailure) {
    // Google calls this when the key is invalid / restricted / API disabled.
    window.gm_authFailure = () => {
      const msg =
        'Google kalitni rad etdi: Cloud Console → APIs (Maps JavaScript, Places, Geocoding) yoqilganmi, ' +
        'kalit cheklovlarida bu domen (https://cyberpitch.uz/*) bormi va billing ulanganmi — tekshiring.'
      window.__solarMapsAuthError = msg
      onAuthFailure?.(new Error(msg))
    }
  }

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
      // Give gm_authFailure a tick to record key errors first.
      setTimeout(() => {
        if (!window.google?.maps) {
          reject(new Error(mapsAuthMessage() || 'Google Maps failed to initialize'))
          return
        }
        resolve(window.google.maps)
      }, 300)
    }
    script.onerror = () => reject(new Error('Could not load Google Maps script'))
    document.head.appendChild(script)
  })

  return loading
}
