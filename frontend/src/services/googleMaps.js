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

/**
 * Official Maps JS bootstrap — enables google.maps.importLibrary('maps'|'places').
 * Required for PlaceAutocompleteElement (Places API New).
 */
function installBootstrap(key) {
  if (typeof window === 'undefined') return
  if (window.google?.maps?.importLibrary) return
  // prettier-ignore
  ;((g) => {
    var h, a, k, p = 'The Google Maps JavaScript API', c = 'google', l = 'importLibrary', q = '__ib__', m = document, b = window
    b = b[c] || (b[c] = {})
    var d = b.maps || (b.maps = {}), r = new Set(), e = new URLSearchParams()
    var u = () => h || (h = new Promise(async (f, n) => {
      await (a = m.createElement('script'))
      e.set('libraries', [...r] + '')
      for (k in g) {
        e.set(k.replace(/[A-Z]/g, (t) => '_' + t[0].toLowerCase()), g[k])
      }
      e.set('callback', c + '.maps.' + q)
      a.src = `https://maps.${c}apis.com/maps/api/js?` + e
      d[q] = f
      a.onerror = () => (h = n(Error(p + ' could not load.')))
      a.nonce = m.querySelector('script[nonce]')?.nonce || ''
      m.head.append(a)
    }))
    if (d[l]) {
      console.warn(p + ' only loads once. Ignoring:', g)
    } else {
      d[l] = (f, ...n) => r.add(f) && u().then(() => d[l](f, ...n))
    }
  })({ key, v: 'weekly' })
}

/** Load Maps JavaScript API once (satellite picker + Places Autocomplete New). */
export function loadGoogleMaps(onAuthFailure) {
  if (typeof window !== 'undefined' && window.google?.maps?.Map && window.google?.maps?.importLibrary) {
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
        'Google rejected the key: in Cloud Console → APIs, check that Maps JavaScript, Places API (New), Geocoding, and Maps Static are enabled, ' +
        'that the key restrictions include Places API (New) + this domain (https://cyberpitch.uz/*), and that billing is enabled.'
      window.__solarMapsAuthError = msg
      onAuthFailure?.(new Error(msg))
    }
  }

  installBootstrap(key)
  loading = (async () => {
    await window.google.maps.importLibrary('maps')
    await window.google.maps.importLibrary('places')
    if (mapsAuthMessage()) {
      throw new Error(mapsAuthMessage())
    }
    if (!window.google?.maps) {
      throw new Error('Google Maps failed to initialize')
    }
    return window.google.maps
  })().catch((err) => {
    loading = null
    throw err
  })

  return loading
}

/** Dynamic library import after bootstrap (e.g. 'places', 'maps', 'geocoding'). */
export async function importMapsLibrary(name) {
  await loadGoogleMaps()
  return window.google.maps.importLibrary(name)
}
